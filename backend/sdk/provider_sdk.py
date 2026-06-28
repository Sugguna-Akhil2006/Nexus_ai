"""Provider SDK Module.

Exposes base interfaces, configs models, capabilities profiles, retry policies,
metrics aggregators, and registries used by all Nexus official capability providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class ProviderSDKError(NexusException):
    """Base exception for all Provider SDK related errors."""
    pass


class ProviderValidationError(ProviderSDKError):
    """Raised when properties configuration validation fails."""
    pass


class ProviderConnectionError(ProviderSDKError):
    """Raised when health check connections fail."""
    pass


# =====================================================================
# Data Models and Enums
# =====================================================================

@dataclass(frozen=True)
class ProviderCapabilities:
    """Capability support flags schema model.

    Attributes:
        chat: True if chat is supported.
        streaming: True if token streaming is supported.
        embeddings: True if dimensional embeddings are supported.
        vision: True if vision modality is supported.
        audio: True if audio processing is supported.
        tool_calling: True if tool calling schema outputs are supported.
        structured_output: True if structured JSON schemas are supported.
        batch_processing: True if batch execution runs are supported.
        function_calling: True if direct function calling is supported.
    """
    chat: bool = False
    streaming: bool = False
    embeddings: bool = False
    vision: bool = False
    audio: bool = False
    tool_calling: bool = False
    structured_output: bool = False
    batch_processing: bool = False
    function_calling: bool = False


@dataclass(frozen=True)
class RetryPolicy:
    """Retries execution limits.

    Attributes:
        mode: Fixed delay or exponential backoff progression.
        max_attempts: Limit of retry runs.
        delay: Sleep delay duration between attempts.
        backoff_factor: Multiplier for backoff progression.
        timeout: Total connection timeout constraint.
        retryable_exceptions: Exception names that trigger retries.
    """
    mode: str = "fixed"  # "fixed" or "exponential"
    max_attempts: int = 3
    delay: float = 1.0
    backoff_factor: float = 2.0
    timeout: float = 30.0
    retryable_exceptions: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProviderConfiguration:
    """Configuration package describing downstream targets credentials.

    Attributes:
        provider_id: Unique string key identifier.
        name: Common name.
        version: Version details.
        endpoint: Destination target URL/endpoint.
        credentials: Key-value credentials dictionary.
        timeout: Downstream calls timeout limit.
        retry_policy: Active retry policies.
        metadata: Extra metrics tags.
    """
    provider_id: str
    name: str
    version: str
    endpoint: str
    credentials: Dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        # Obfuscate credentials dictionary to prevent logging secrets
        masked = {k: "********" for k in self.credentials.keys()}
        return (
            f"ProviderConfiguration(provider_id='{self.provider_id}', name='{self.name}', "
            f"version='{self.version}', endpoint='{self.endpoint}', credentials={masked}, "
            f"timeout={self.timeout})"
        )


# =====================================================================
# Metrics
# =====================================================================

class ProviderMetrics:
    """Uptime, tokens, latency, and success rates recorder."""

    def __init__(self) -> None:
        self._requests = 0
        self._successes = 0
        self._failures = 0
        self._total_latency = 0.0
        self._token_usage = 0
        self._uptime_start = time.time()
        self._lock = threading.RLock()

    def record(self, success: bool, latency: float, tokens: int = 0) -> None:
        """Saves execution statistics parameters thread-safely."""
        with self._lock:
            self._requests += 1
            if success:
                self._successes += 1
            else:
                self._failures += 1
            self._total_latency += latency
            self._token_usage += tokens

    @property
    def average_latency(self) -> float:
        """Retrieves average delay."""
        with self._lock:
            return self._total_latency / self._requests if self._requests > 0 else 0.0

    @property
    def success_rate(self) -> float:
        """Retrieves success rate metrics ratio."""
        with self._lock:
            return self._successes / self._requests if self._requests > 0 else 1.0

    @property
    def uptime(self) -> float:
        """Retrieves elapsed uptime duration."""
        with self._lock:
            return time.time() - self._uptime_start

    @property
    def metrics(self) -> Dict[str, Any]:
        """Retrieves statistics copy."""
        with self._lock:
            return {
                "requests": self._requests,
                "success_rate": self.success_rate,
                "failures": self._failures,
                "average_latency": self.average_latency,
                "token_usage": self._token_usage,
                "uptime": self.uptime
            }


# =====================================================================
# Base Provider Contract
# =====================================================================

class BaseProvider(ABC):
    """Abstract Base Class specifying official provider lifecycles."""

    def __init__(self, config: ProviderConfiguration) -> None:
        self._config = config
        self._metrics = ProviderMetrics()
        self._logger = StructuredLogger()
        self._event_bus = EventBus()
        self._lock = threading.RLock()
        self._active = False

    @property
    def config(self) -> ProviderConfiguration:
        """Retrieves provider configurations."""
        return self._config

    @property
    def metrics(self) -> ProviderMetrics:
        """Retrieves provider statistics metrics."""
        return self._metrics

    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        """Retrieves capabilities support details flags."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Prepares database tables or endpoints initialization details."""
        pass

    def configure(self, config: ProviderConfiguration) -> None:
        """Dynamically reconfigures provider configurations."""
        with self._lock:
            self._config = config
            self._logger.info(f"Provider '{self._config.provider_id}' reconfigured.")

    def start(self) -> None:
        """Activates connection loops."""
        with self._lock:
            self._active = True
            self._publish_event("provider.started")
            self._logger.info(f"Provider '{self._config.provider_id}' started.")

    def stop(self) -> None:
        """Deactivates active loops."""
        with self._lock:
            self._active = False
            self._publish_event("provider.stopped")
            self._logger.info(f"Provider '{self._config.provider_id}' stopped.")

    def shutdown(self) -> None:
        """Disposes resources and shuts down execution context."""
        self.stop()
        self._logger.info(f"Provider '{self._config.provider_id}' shut down.")

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection integrity status."""
        pass

    def supports(self, capability: str) -> bool:
        """Queries support flags."""
        caps = self.capabilities
        mapping = {
            "chat": caps.chat,
            "streaming": caps.streaming,
            "embeddings": caps.embeddings,
            "vision": caps.vision,
            "audio": caps.audio,
            "tool_calling": caps.tool_calling,
            "structured_output": caps.structured_output,
            "batch_processing": caps.batch_processing,
            "function_calling": caps.function_calling
        }
        return mapping.get(capability.lower().strip(), False)

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="BaseProvider",
            payload={"event_name": event_name, "provider_id": self._config.provider_id, **kwargs}
        )
        self._event_bus.publish(event)


# =====================================================================
# Provider Registry
# =====================================================================

class ProviderRegistry:
    """Thread-safe registry routing registrations."""

    _instance: Optional["ProviderRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ProviderRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._providers: Dict[str, BaseProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider: BaseProvider) -> None:
        """Registers a BaseProvider plugin."""
        if not provider:
            raise ProviderValidationError("provider instance cannot be None.")
        pid = provider.config.provider_id
        if not pid or not str(pid).strip():
            raise ProviderValidationError("provider_id cannot be empty.")

        with self._lock:
            if pid in self._providers:
                raise ProviderValidationError(f"Provider '{pid}' already registered.")
            self._providers[pid] = provider
            self._logger.info(f"Registered provider: {pid}")

        # Publish Event
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProviderRegistry",
            payload={"event_name": "provider.registered", "provider_id": pid}
        )
        EventBus().publish(event)

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a provider registration."""
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderValidationError(f"Provider '{provider_id}' not found.")
            prov = self._providers[provider_id]
            prov.shutdown()
            del self._providers[provider_id]
            self._logger.info(f"Unregistered provider: {provider_id}")

    def get_provider(self, provider_id: str) -> BaseProvider:
        """Retrieves registered provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise ProviderValidationError(f"Provider '{provider_id}' not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[BaseProvider]:
        """Lists active providers."""
        with self._lock:
            return list(self._providers.values())

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers."""
        with self._lock:
            results = {}
            for pid, prov in self._providers.items():
                try:
                    results[pid] = prov.health_check()
                    prov._publish_event("provider.health.checked", status=results[pid])
                except Exception:
                    results[pid] = False
                    prov._publish_event("provider.health.checked", status=False)
            return results


# =====================================================================
# Error Mapper
# =====================================================================

class ErrorMapper:
    """Helper converting exceptions to standardized ProviderSDKError."""

    @staticmethod
    def map_exception(e: Exception) -> Exception:
        """Transforms errors."""
        if isinstance(e, ProviderSDKError):
            return e
        return ProviderSDKError(f"Provider SDK mapped external exception: {e}")


# =====================================================================
# Mock Provider Implementation
# =====================================================================

class MockDatabaseProvider(BaseProvider):
    """Mock database provider implementing BaseProvider."""

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            chat=False,
            streaming=False,
            embeddings=True,
            tool_calling=True
        )

    def initialize(self) -> None:
        pass

    def health_check(self) -> bool:
        return True
