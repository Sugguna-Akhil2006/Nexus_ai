"""OpenAI Provider Plugin Module.

Implements the ModelProvider interface for OpenAI API integration, using standard
urllib.request calls to avoid external dependency requirements.
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


# =====================================================================
# Configuration
# =====================================================================

@dataclass(frozen=True)
class RetryPolicy:
    """Immutable config settings governing backoff retries.

    Attributes:
        max_retries: Limit of retries to attempt.
        initial_delay: Baseline sleep delay in seconds.
        backoff_factor: Multiplier for backoff progression.
        retryable_status_codes: Set of HTTP status codes to retry.
    """
    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    retryable_status_codes: Set[int] = field(default_factory=lambda: {429, 500, 502, 503, 504})


@dataclass(frozen=True)
class ProviderConfiguration:
    """Immutable configuration package for the OpenAI provider.

    Attributes:
        api_key: Secret API credential token.
        base_url: Target REST url endpoint.
        organization: Optional organization header tag.
        timeout: Client connection timeout limits.
        retry_policy: Retries backoff configurations.
        metadata: Extra options mapping.
    """
    api_key: str
    base_url: str = "https://api.openai.com/v1"
    organization: Optional[str] = None
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        # Obfuscate credentials to prevent secret leaks
        masked = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "********"
        return (
            f"ProviderConfiguration(api_key='{masked}', base_url='{self.base_url}', "
            f"organization={self.organization}, timeout={self.timeout})"
        )


# =====================================================================
# Metrics
# =====================================================================

class ProviderMetrics:
    """Thread-safe catalog monitoring execution statistics."""

    def __init__(self) -> None:
        self._requests = 0
        self._tokens = 0
        self._latency = 0.0
        self._errors = 0
        self._rate_limit_remaining = 1000
        self._lock = threading.RLock()

    def record(self, tokens: int, latency: float, success: bool, rate_limit: Optional[int] = None) -> None:
        """Saves metrics values safely."""
        with self._lock:
            self._requests += 1
            self._tokens += tokens
            self._latency += latency
            if not success:
                self._errors += 1
            if rate_limit is not None:
                self._rate_limit_remaining = rate_limit

    @property
    def metrics(self) -> Dict[str, Any]:
        """Retrieves snapshots copy."""
        with self._lock:
            return {
                "requests": self._requests,
                "tokens": self._tokens,
                "latency": self._latency,
                "errors": self._errors,
                "rate_limit_remaining": self._rate_limit_remaining
            }


# =====================================================================
# Error Mapper
# =====================================================================

class ErrorMapper:
    """Helper converting HTTP and protocol exception types into Nexus ModelErrors."""

    @staticmethod
    def map_exception(e: Exception, model_id: str) -> ModelError:
        """Converts error classes."""
        if isinstance(e, urllib.error.HTTPError):
            code = e.code
            body_str = ""
            try:
                body_str = e.read().decode("utf-8")
            except Exception:
                pass

            message = f"OpenAI HTTP error {code}: {body_str or e.reason}"

            if code == 404:
                return ModelNotFoundError(f"Model or path '{model_id}' not found. {message}")
            elif code in [400, 422]:
                return ModelValidationError(f"Invalid request parameters for '{model_id}'. {message}")
            elif code == 401:
                return ModelValidationError(f"Unauthorized credentials. {message}")
            else:
                return ModelError(message)

        if isinstance(e, urllib.error.URLError):
            return ModelError(f"Connection failure to OpenAI provider endpoint: {e.reason}")

        if isinstance(e, ModelError):
            return e

        return ModelError(f"Internal provider exception: {e}")


# =====================================================================
# Streaming Adapter
# =====================================================================

class StreamingAdapter:
    """Helper converting Server-Sent Events (SSE) data lines into InferenceResponses."""

    @staticmethod
    def parse_sse_line(line: str) -> Optional[Dict[str, Any]]:
        """Extracts JSON dictionaries from SSE data: protocol prefixes."""
        clean = line.strip()
        if not clean.startswith("data:"):
            return None
        payload = clean[5:].strip()
        if payload == "[DONE]":
            return None
        try:
            return json.loads(payload)
        except Exception:
            return None


# =====================================================================
# OpenAI Provider
# =====================================================================

class OpenAIProvider(ModelProvider):
    """Adapter connecting the Nexus model capabilities framework directly with OpenAI REST endpoints."""

    def __init__(self, config: ProviderConfiguration) -> None:
        self.config = config
        self.metrics = ProviderMetrics()
        self.logger = StructuredLogger()
        self.event_bus = EventBus()

        self._publish_event("provider.connected", provider="openai")

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self._publish_event("provider.request.started", model=request.model)
        start_time = time.perf_counter()

        # Handle Mock validation / local simulations
        if self.config.base_url.startswith("mock://") or self.config.api_key == "mock-key":
            latency = 0.05
            content = f"Mock OpenAI response for: {request.prompt or 'hello'}"
            # Check for simulated error trigger
            if request.metadata.get("trigger_error", False):
                raise ModelValidationError("Simulated OpenAI Validation error.")

            self.metrics.record(tokens=25, latency=latency, success=True)
            self._publish_event("provider.request.completed", model=request.model)
            return InferenceResponse(
                request_id=str(uuid.uuid4()),
                content=content,
                finish_reason="stop",
                token_usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
                latency=latency,
                provider="openai",
                model=request.model
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization

        # Construct request payload
        messages = request.messages
        if not messages and request.prompt:
            messages = [{"role": "user", "content": request.prompt}]

        payload = {
            "model": request.model,
            "messages": messages,
            **request.parameters
        }

        url = f"{self.config.base_url}/chat/completions"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        # Execute call with RetryPolicy backoff
        latency = 0.0
        success = False
        tokens = 0
        response_body = {}

        policy = self.config.retry_policy
        for attempt in range(policy.max_retries + 1):
            try:
                attempt_start = time.perf_counter()
                with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                    raw_data = response.read()
                    response_body = json.loads(raw_data.decode("utf-8"))
                    latency = time.perf_counter() - attempt_start
                    success = True

                    # Check rate limits remaining header
                    rl_header = response.headers.get("x-ratelimit-remaining-requests")
                    rate_limit = int(rl_header) if rl_header else None

                    # Usage tokens metrics
                    usage = response_body.get("usage", {})
                    tokens = usage.get("total_tokens", 0)

                    self.metrics.record(tokens=tokens, latency=latency, success=True, rate_limit=rate_limit)
                    break

            except Exception as exc:
                latency = time.perf_counter() - attempt_start
                # Evaluate retry eligibility
                is_retryable = False
                if isinstance(exc, urllib.error.HTTPError):
                    if exc.code in policy.retryable_status_codes:
                        is_retryable = True

                if is_retryable and attempt < policy.max_retries:
                    delay = policy.initial_delay * (policy.backoff_factor ** attempt)
                    self.logger.warning(
                        f"Retrying OpenAI call to {request.model}. Attempt {attempt+1}/{policy.max_retries}. Delay {delay}s."
                    )
                    time.sleep(delay)
                else:
                    self.metrics.record(tokens=0, latency=latency, success=False)
                    self._publish_event("provider.failed", model=request.model, error=str(exc))
                    raise ErrorMapper.map_exception(exc, request.model)

        self._publish_event("provider.request.completed", model=request.model)
        choice = response_body.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")

        return InferenceResponse(
            request_id=response_body.get("id", str(uuid.uuid4())),
            content=content,
            finish_reason=choice.get("finish_reason", "stop"),
            token_usage=response_body.get("usage", {}),
            latency=latency,
            provider="openai",
            model=request.model,
            metadata=response_body
        )

    def generate_stream(self, request: InferenceRequest) -> Iterator[InferenceResponse]:
        self._publish_event("provider.stream.started", model=request.model)

        # Mock streaming implementation
        if self.config.base_url.startswith("mock://") or self.config.api_key == "mock-key":
            content = f"Mock streaming response answer."
            words = content.split(" ")
            for idx, word in enumerate(words):
                yield InferenceResponse(
                    request_id=str(uuid.uuid4()),
                    content=word + " " if idx < len(words) - 1 else word,
                    finish_reason="stop" if idx == len(words) - 1 else "",
                    token_usage={"total_tokens": 1},
                    latency=0.01,
                    provider="openai",
                    model=request.model
                )
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization

        messages = request.messages
        if not messages and request.prompt:
            messages = [{"role": "user", "content": request.prompt}]

        payload = {
            "model": request.model,
            "messages": messages,
            "stream": True,
            **request.parameters
        }

        url = f"{self.config.base_url}/chat/completions"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                for line in response:
                    decoded = line.decode("utf-8").strip()
                    if not decoded:
                        continue
                    parsed = StreamingAdapter.parse_sse_line(decoded)
                    if not parsed:
                        continue

                    choice = parsed.get("choices", [{}])[0]
                    delta = choice.get("delta", {})
                    content_chunk = delta.get("content", "")
                    finish_reason = choice.get("finish_reason") or ""

                    yield InferenceResponse(
                        request_id=parsed.get("id", str(uuid.uuid4())),
                        content=content_chunk,
                        finish_reason=finish_reason,
                        token_usage={},
                        latency=0.0,
                        provider="openai",
                        model=request.model,
                        metadata=parsed
                    )
        except Exception as exc:
            self._publish_event("provider.failed", model=request.model, error=str(exc))
            raise ErrorMapper.map_exception(exc, request.model)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self._publish_event("provider.request.started", model=request.model)
        start_time = time.perf_counter()

        # Mock embedding implementation
        if self.config.base_url.startswith("mock://") or self.config.api_key == "mock-key":
            latency = 0.02
            self.metrics.record(tokens=5, latency=latency, success=True)
            self._publish_event("provider.request.completed", model=request.model)
            return EmbeddingResponse(
                request_id=str(uuid.uuid4()),
                embeddings=[[0.1] * 1536],
                token_usage={"total_tokens": 5},
                latency=latency,
                provider="openai",
                model=request.model
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}"
        }
        if self.config.organization:
            headers["OpenAI-Organization"] = self.config.organization

        payload = {
            "model": request.model,
            "input": request.input,
            **request.parameters
        }

        url = f"{self.config.base_url}/embeddings"
        req_obj = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        latency = 0.0
        response_body = {}
        try:
            attempt_start = time.perf_counter()
            with urllib.request.urlopen(req_obj, timeout=self.config.timeout) as response:
                raw_data = response.read()
                response_body = json.loads(raw_data.decode("utf-8"))
                latency = time.perf_counter() - attempt_start

                usage = response_body.get("usage", {})
                tokens = usage.get("total_tokens", 0)

                self.metrics.record(tokens=tokens, latency=latency, success=True)
        except Exception as exc:
            latency = time.perf_counter() - attempt_start
            self.metrics.record(tokens=0, latency=latency, success=False)
            self._publish_event("provider.failed", model=request.model, error=str(exc))
            raise ErrorMapper.map_exception(exc, request.model)

        self._publish_event("provider.request.completed", model=request.model)
        embeddings = [item.get("embedding", []) for item in response_body.get("data", [])]

        return EmbeddingResponse(
            request_id=str(uuid.uuid4()),
            embeddings=embeddings,
            token_usage=response_body.get("usage", {}),
            latency=latency,
            provider="openai",
            model=request.model,
            metadata=response_body
        )

    def list_models(self) -> List[ModelInfo]:
        # Predefined static models catalog cache
        return [
            ModelInfo(
                model_id="gpt-4o",
                provider="openai",
                name="GPT-4o Chat Model",
                version="1.0.0",
                context_window=128000,
                max_output_tokens=4096,
                supported_modalities=["text", "image"],
                capabilities=[
                    ModelCapability.CHAT,
                    ModelCapability.COMPLETION,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                    ModelCapability.STRUCTURED_OUTPUT,
                    ModelCapability.MULTIMODAL
                ]
            ),
            ModelInfo(
                model_id="text-embedding-3-small",
                provider="openai",
                name="Text Embedding 3 Small",
                version="1.0.0",
                context_window=8191,
                max_output_tokens=0,
                supported_modalities=["text"],
                capabilities=[ModelCapability.EMBEDDING]
            )
        ]

    def get_model(self, model_id: str) -> ModelInfo:
        for model in self.list_models():
            if model.model_id == model_id:
                return model
        raise ModelNotFoundError(f"Model '{model_id}' not found in OpenAI provider catalog.")

    def health_check(self) -> bool:
        if self.config.base_url.startswith("mock://") or self.config.api_key == "mock-key":
            return True

        # Perform quick GET call to base URL to inspect downstream connectivity
        try:
            url = f"{self.config.base_url}/models"
            headers = {"Authorization": f"Bearer {self.config.api_key}"}
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=5.0) as response:
                return response.status == 200
        except Exception:
            return False

    def supports(self, capability: ModelCapability) -> bool:
        # Check overall capabilities maps intersection
        supported_caps = {
            ModelCapability.CHAT,
            ModelCapability.COMPLETION,
            ModelCapability.STREAMING,
            ModelCapability.EMBEDDING,
            ModelCapability.FUNCTION_CALLING,
            ModelCapability.STRUCTURED_OUTPUT,
            ModelCapability.MULTIMODAL
        }
        return capability in supported_caps

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="OpenAIProvider",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
