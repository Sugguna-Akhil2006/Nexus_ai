"""Ollama Provider Plugin Module.

Implements the ModelProvider interface for Ollama local LLM integration,
inheriting from BaseProvider to utilize standard SDK metrics, logging, and events.
"""

from dataclasses import dataclass, field
import datetime
import json
import logging
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Set, Union
import urllib.error
import urllib.request
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger
from backend.interfaces.model import (
    ModelProvider,
    InferenceRequest,
    InferenceResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ModelCapability,
    ModelError,
    ModelValidationError,
    ModelNotFoundError,
    UnsupportedCapabilityError,
)
from backend.sdk.provider_sdk import (
    BaseProvider,
    ProviderConfiguration,
    ProviderCapabilities,
    RetryPolicy,
    ProviderSDKError,
    ErrorMapper as SDKErrorMapper
)


# =====================================================================
# Configuration
# =====================================================================

@dataclass(frozen=True)
class OllamaConfiguration:
    """Immutable config settings specific to local Ollama endpoints.

    Attributes:
        host: Downstream host address (e.g. localhost or 127.0.0.1).
        port: Listening port.
        timeout: Network request connection timeouts.
        retry_policy: Retries backoff configurations.
        metadata: Extra options mapping.
    """
    host: str = "localhost"
    port: int = 11434
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Error Mapper
# =====================================================================

class ErrorMapper:
    """Translates HTTP connection errors to standard Nexus Exceptions."""

    @staticmethod
    def map_exception(e: Exception, model_id: str) -> ModelError:
        """Standardizes exception conversions."""
        if isinstance(e, urllib.error.HTTPError):
            code = e.code
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                pass
            msg = f"Ollama HTTP error {code}: {body or e.reason}"
            if code == 404:
                return ModelNotFoundError(f"Model '{model_id}' not found. {msg}")
            return ModelValidationError(msg)

        if isinstance(e, urllib.error.URLError):
            return ModelError(f"Ollama connection failure. Service might not be running: {e.reason}")

        if isinstance(e, ModelError):
            return e

        return ModelError(f"Internal Ollama provider exception: {e}")


# =====================================================================
# Provider State Telemetry
# =====================================================================

from datetime import datetime

@dataclass
class ProviderState:
    connected: bool = False
    provider: str = "ollama"
    model: str = "llama3"
    latency_ms: float = 0.0
    last_error: str = ""
    last_checked: str = ""
    fallback: bool = True


# =====================================================================
# Ollama Provider
# =====================================================================

class OllamaProvider(BaseProvider, ModelProvider):
    """Local LLM provider adapter connecting Nexus core models with local Ollama APIs."""

    def __init__(self, config: OllamaConfiguration) -> None:
        # Map to Provider SDK Base configuration
        p_config = ProviderConfiguration(
            provider_id="ollama",
            name="Ollama Local LLM Provider",
            version="1.0.0",
            endpoint=f"http://{config.host}:{config.port}",
            timeout=config.timeout,
            retry_policy=config.retry_policy,
            metadata=config.metadata
        )
        super().__init__(p_config)
        self.ollama_config = config
        self._cached_models: List[ModelInfo] = []
        self.downloaded_models: List[str] = []

        # State and background monitor
        self.provider_state = ProviderState(provider="ollama")
        self._monitor_thread = threading.Thread(target=self._connection_monitor, daemon=True)
        self._monitor_thread.start()

        self._publish_event("provider.connected", provider="ollama")

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Declares capabilities flags."""
        return ProviderCapabilities(
            chat=True,
            streaming=True,
            embeddings=True,
            tool_calling=False,
            structured_output=True,
            function_calling=False
        )

    def initialize(self) -> None:
        """Initializes and runs synchronous check on startup."""
        self._logger.info("Initializing Ollama Provider")
        self._check_connection()

    def _check_connection(self) -> None:
        self._logger.info("Checking localhost:11434")
        start_time = time.perf_counter()
        try:
            url = f"http://{self.ollama_config.host}:{self.ollama_config.port}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=1.5) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]

            latency = (time.perf_counter() - start_time) * 1000.0

            # Update state parameters
            self.provider_state.connected = True
            self.provider_state.fallback = False
            self.provider_state.latency_ms = round(latency, 2)
            self.provider_state.last_error = ""
            self.provider_state.last_checked = datetime.utcnow().isoformat()

            # Refresh local models catalog representation
            discovered = []
            for item in data.get("models", []):
                name = item.get("name", "unknown")
                capabilities = [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.STREAMING]
                if "embed" in name or "minilm" in name:
                    capabilities = [ModelCapability.EMBEDDING]

                discovered.append(ModelInfo(
                    model_id=name,
                    provider="ollama",
                    name=name.split(":")[0].capitalize(),
                    version=name.split(":")[-1] if ":" in name else "latest",
                    context_window=4096,
                    max_output_tokens=2048,
                    supported_modalities=["text"],
                    capabilities=capabilities,
                    metadata=item
                ))
            self._cached_models = discovered

            if models:
                self.downloaded_models = models
                self.provider_state.model = models[0]
            else:
                self.downloaded_models = []
                self.provider_state.model = "llama3"

            self._logger.info(f"Ollama connection successful. Detected models: {models}. Provider Ready.")

        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000.0
            self.provider_state.connected = False
            self.provider_state.fallback = True
            self.provider_state.latency_ms = round(latency, 2)
            self.provider_state.last_error = str(e)
            self.provider_state.last_checked = datetime.utcnow().isoformat()
            self.provider_state.model = "llama3"
            self.downloaded_models = []
            self._logger.warning(f"Connection failed. Reason: {e}. Switching to Mock Provider.")

    def _connection_monitor(self) -> None:
        self._logger.info("Initializing Ollama Provider connection monitor thread")
        while True:
            self._check_connection()
            time.sleep(5.0)

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self._publish_event("provider.request.started", model=request.model)
        start_time = time.perf_counter()

        model_name = request.model
        chat_models = [m.model_id for m in self._cached_models if ModelCapability.CHAT in m.capabilities]
        is_mock_config = self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False)

        # Handle Mock URL / offline tests fallback
        if is_mock_config or not self.provider_state.connected or not chat_models:
            latency = 0.05
            content = f"Mock local Ollama response matching '{request.prompt or 'hello'}'"
            self.metrics.record(success=True, latency=latency)
            self._publish_event("provider.request.completed", model=request.model)
            return InferenceResponse(
                request_id=str(uuid.uuid4()),
                content=content,
                finish_reason="stop",
                token_usage={"total_tokens": 30},
                latency=latency,
                provider="ollama",
                model=request.model
            )

        # Auto model detection logic
        if model_name != "mock-chat-model":
            if model_name not in chat_models and f"{model_name}:latest" not in chat_models:
                self._logger.warning("Configured model '%s' not found locally. Falling back to default model '%s'.", model_name, chat_models[0])
                model_name = chat_models[0]
        else:
            model_name = chat_models[0]

        headers = {"Content-Type": "application/json"}
        messages = request.messages
        if not messages and request.prompt:
            messages = [{"role": "user", "content": request.prompt}]

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": request.parameters
        }

        url = f"{self.config.endpoint}/api/chat"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        latency = 0.0
        success = False
        response_body = {}

        policy = self.config.retry_policy
        for attempt in range(policy.max_attempts + 1):
            try:
                attempt_start = time.perf_counter()
                with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                    raw_data = response.read()
                    response_body = json.loads(raw_data.decode("utf-8"))
                    latency = time.perf_counter() - attempt_start
                    success = True
                    self.metrics.record(success=True, latency=latency)
                    break
            except Exception as exc:
                latency = time.perf_counter() - attempt_start
                if attempt < policy.max_attempts:
                    delay = policy.delay * (policy.backoff_factor ** attempt)
                    self.logger.warning(f"Ollama call retry. Attempt {attempt+1}/{policy.max_attempts}. Delay {delay}s.")
                    time.sleep(delay)
                else:
                    self.metrics.record(success=False, latency=latency)
                    self._publish_event("provider.failed", model=request.model, error=str(exc))
                    raise ErrorMapper.map_exception(exc, request.model)

        self._publish_event("provider.request.completed", model=request.model)
        message_obj = response_body.get("message", {})
        content = message_obj.get("content", "")

        return InferenceResponse(
            request_id=str(uuid.uuid4()),
            content=content,
            finish_reason="stop" if response_body.get("done", True) else "",
            token_usage={"total_tokens": response_body.get("eval_count", 0) + response_body.get("prompt_eval_count", 0)},
            latency=latency,
            provider="ollama",
            model=request.model,
            metadata=response_body
        )

    def generate_stream(self, request: InferenceRequest) -> Iterator[InferenceResponse]:
        self._publish_event("provider.stream.started", model=request.model)

        model_name = request.model
        chat_models = [m.model_id for m in self._cached_models if ModelCapability.CHAT in m.capabilities]
        is_mock_config = self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False)

        # Fall back to mock stream ONLY when mock host is forced, unreachable, or no local models are available
        if is_mock_config or not self.provider_state.connected or not chat_models:
            query = ""
            if request.messages:
                query = request.messages[-1].get("content", "")
            elif request.prompt:
                query = request.prompt

            query_lower = query.lower().strip()
            if any(greet in query_lower for greet in ["hi", "hello", "hey", "greetings"]):
                content = "Hello! I am your local Ollama assistant. How can I help you today?"
            elif "how are you" in query_lower:
                content = "I am doing great, thank you for asking! How is your agent workspace setup going?"
            else:
                content = "Mock streaming words local."

            words = content.split(" ")
            for idx, word in enumerate(words):
                yield InferenceResponse(
                    request_id=str(uuid.uuid4()),
                    content=word + " " if idx < len(words) - 1 else word,
                    finish_reason="stop" if idx == len(words) - 1 else "",
                    token_usage={"total_tokens": 1},
                    latency=0.01,
                    provider="ollama",
                    model=request.model
                )
            return

        # Auto model detection logic
        if model_name != "mock-chat-model":
            if model_name not in chat_models and f"{model_name}:latest" not in chat_models:
                self._logger.warning("Configured model '%s' not found locally. Falling back to default model '%s'.", model_name, chat_models[0])
                model_name = chat_models[0]
        else:
            model_name = chat_models[0]

        headers = {"Content-Type": "application/json"}
        messages = request.messages
        if not messages and request.prompt:
            messages = [{"role": "user", "content": request.prompt}]

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": True,
            "options": request.parameters
        }

        url = f"{self.config.endpoint}/api/chat"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                for line in response:
                    decoded = line.decode("utf-8").strip()
                    if not decoded:
                        continue
                    parsed = json.loads(decoded)
                    message_obj = parsed.get("message", {})
                    content_chunk = message_obj.get("content", "")
                    done = parsed.get("done", False)

                    yield InferenceResponse(
                        request_id=str(uuid.uuid4()),
                        content=content_chunk,
                        finish_reason="stop" if done else "",
                        token_usage={},
                        latency=0.0,
                        provider="ollama",
                        model=request.model,
                        metadata=parsed
                    )
        except Exception as exc:
            self._publish_event("provider.failed", model=request.model, error=str(exc))
            # Fallback to local mock streaming for offline developer manual tests
            msg = f"Mock local fallback stream (Local Ollama model '{request.model}' was not found or offline: {exc})."
            words = msg.split(" ")
            for idx, word in enumerate(words):
                yield InferenceResponse(
                    request_id=str(uuid.uuid4()),
                    content=word + " " if idx < len(words) - 1 else word,
                    finish_reason="stop" if idx == len(words) - 1 else "",
                    token_usage={"total_tokens": 1},
                    latency=0.01,
                    provider="ollama",
                    model=request.model
                )

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._publish_event("provider.request.started", model=request.model)
        start_time = time.perf_counter()

        if self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False):
            latency = 0.02
            self.metrics.record(success=True, latency=latency)
            self._publish_event("provider.request.completed", model=request.model)
            return EmbeddingResponse(
                request_id=str(uuid.uuid4()),
                embeddings=[[0.05] * 768],
                token_usage={"total_tokens": 10},
                latency=latency,
                provider="ollama",
                model=request.model
            )

        headers = {"Content-Type": "application/json"}
        payload = {
            "model": request.model,
            "prompt": request.input if isinstance(request.input, str) else request.input[0],
            "options": request.parameters
        }

        url = f"{self.config.endpoint}/api/embeddings"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        latency = 0.0
        response_body = {}
        try:
            attempt_start = time.perf_counter()
            with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                raw_data = response.read()
                response_body = json.loads(raw_data.decode("utf-8"))
                latency = time.perf_counter() - attempt_start
                self.metrics.record(success=True, latency=latency)
        except Exception as exc:
            latency = time.perf_counter() - attempt_start
            self.metrics.record(success=False, latency=latency)
            self._publish_event("provider.failed", model=request.model, error=str(exc))
            raise ErrorMapper.map_exception(exc, request.model)

        self._publish_event("provider.request.completed", model=request.model)
        embedding = response_body.get("embedding", [])

        return EmbeddingResponse(
            request_id=str(uuid.uuid4()),
            embeddings=[embedding],
            token_usage={},
            latency=latency,
            provider="ollama",
            model=request.model,
            metadata=response_body
        )

    def pull_model(self, model_id: str) -> None:
        """Downloads/pulls a local model from Ollama library registry.

        Args:
            model_id: Target model ID string.
        """
        self._publish_event("provider.request.started", model=model_id)

        if self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False):
            self._publish_event("provider.model.pulled", model=model_id)
            return

        headers = {"Content-Type": "application/json"}
        payload = {"name": model_id, "stream": False}
        url = f"{self.config.endpoint}/api/pull"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req_obj, timeout=300.0) as response:
                response.read()
                self._publish_event("provider.model.pulled", model=model_id)
        except Exception as exc:
            self._publish_event("provider.failed", model=model_id, error=str(exc))
            raise ErrorMapper.map_exception(exc, model_id)

    def delete_model(self, model_id: str) -> None:
        """Removes/deletes a local model from Ollama library registry.

        Args:
            model_id: Target model ID string.
        """
        if self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False):
            return

        headers = {"Content-Type": "application/json"}
        payload = {"name": model_id}
        url = f"{self.config.endpoint}/api/delete"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                response.read()
        except Exception as exc:
            raise ErrorMapper.map_exception(exc, model_id)

    def list_models(self) -> List[ModelInfo]:
        if self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False):
            if not self._cached_models:
                self._cached_models = [
                    ModelInfo(
                        model_id="llama3",
                        provider="ollama",
                        name="Llama 3 8B",
                        version="latest",
                        context_window=8192,
                        max_output_tokens=2048,
                        supported_modalities=["text"],
                        capabilities=[ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.STREAMING]
                    ),
                    ModelInfo(
                        model_id="nomic-embed-text",
                        provider="ollama",
                        name="Nomic Embed Text",
                        version="latest",
                        context_window=2048,
                        max_output_tokens=0,
                        supported_modalities=["text"],
                        capabilities=[ModelCapability.EMBEDDING]
                    )
                ]
            return self._cached_models

        headers = {"Accept": "application/json"}
        url = f"{self.config.endpoint}/api/tags"
        req_obj = urllib.request.Request(url, headers=headers, method="GET")

        try:
            with urllib.request.urlopen(req_obj, timeout=5.0) as response:
                raw_data = response.read()
                data = json.loads(raw_data.decode("utf-8"))

                discovered = []
                for item in data.get("models", []):
                    name = item.get("name", "unknown")
                    # Deduce capabilities heuristics
                    capabilities = [ModelCapability.CHAT, ModelCapability.COMPLETION, ModelCapability.STREAMING]
                    if "embed" in name or "minilm" in name:
                        capabilities = [ModelCapability.EMBEDDING]

                    discovered.append(ModelInfo(
                        model_id=name,
                        provider="ollama",
                        name=name.split(":")[0].capitalize(),
                        version=name.split(":")[-1] if ":" in name else "latest",
                        context_window=4096,
                        max_output_tokens=2048,
                        supported_modalities=["text"],
                        capabilities=capabilities,
                        metadata=item
                    ))
                self._cached_models = discovered
                return discovered
        except Exception:
            return self._cached_models

    def get_model(self, model_id: str) -> ModelInfo:
        for model in self.list_models():
            if model.model_id == model_id:
                return model
        raise ModelNotFoundError(f"Model '{model_id}' not found in Ollama local catalog.")

    def health_check(self) -> bool:
        if self.ollama_config.host.startswith("mock") or self.ollama_config.metadata.get("mock", False):
            return True

        try:
            url = f"{self.config.endpoint}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as response:
                return response.status == 200
        except Exception:
            return False

    def supports(self, capability: ModelCapability) -> bool:
        supported_caps = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
            ModelCapability.EMBEDDING
        }
        return capability in supported_caps
