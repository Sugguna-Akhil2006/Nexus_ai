"""ProviderBuilder - configures LLM provider settings for ADK agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProviderConfig:
    """Resolved LLM provider configuration.

    Attributes:
        provider_id: Provider identifier (e.g. ``"openai"``, ``"gemini"``).
        model_id: Default model identifier.
        api_key_env: Environment variable name holding the API key.
        base_url: Optional custom API base URL.
        timeout_seconds: Request timeout in seconds.
        max_tokens: Maximum tokens per request.
        temperature: Sampling temperature (0.0-2.0).
        streaming: Whether to enable streaming responses.
        options: Additional provider-specific options.
    """

    provider_id: str = "openai"
    model_id: str = "gpt-4"
    api_key_env: str = "OPENAI_API_KEY"
    base_url: str = ""
    timeout_seconds: float = 60.0
    max_tokens: int = 4096
    temperature: float = 0.7
    streaming: bool = False
    options: Dict[str, Any] = field(default_factory=dict)


class ProviderBuilder:
    """Fluent builder for LLM provider configuration.

    Example::

        provider = (
            ProviderBuilder()
            .provider("openai")
            .model("gpt-4")
            .api_key_env("OPENAI_API_KEY")
            .temperature(0.5)
            .streaming(True)
            .build()
        )
    """

    def __init__(self) -> None:
        self._provider_id: str = "openai"
        self._model_id: str = "gpt-4"
        self._api_key_env: str = "OPENAI_API_KEY"
        self._base_url: str = ""
        self._timeout: float = 60.0
        self._max_tokens: int = 4096
        self._temperature: float = 0.7
        self._streaming: bool = False
        self._options: Dict[str, Any] = {}

    def provider(self, provider_id: str) -> "ProviderBuilder":
        """Sets the provider identifier.

        Args:
            provider_id: Provider name (e.g. ``"openai"``, ``"gemini"``, ``"ollama"``).

        Returns:
            Self for method chaining.
        """
        self._provider_id = provider_id
        return self

    def model(self, model_id: str) -> "ProviderBuilder":
        """Sets the model identifier.

        Args:
            model_id: Model name string.

        Returns:
            Self for method chaining.
        """
        self._model_id = model_id
        return self

    def api_key_env(self, env_var: str) -> "ProviderBuilder":
        """Sets the environment variable name for the API key.

        Args:
            env_var: Environment variable name (e.g. ``"OPENAI_API_KEY"``).

        Returns:
            Self for method chaining.
        """
        self._api_key_env = env_var
        return self

    def base_url(self, url: str) -> "ProviderBuilder":
        """Sets a custom API base URL (for self-hosted or proxy endpoints).

        Args:
            url: Base URL string.

        Returns:
            Self for method chaining.
        """
        self._base_url = url
        return self

    def timeout(self, seconds: float) -> "ProviderBuilder":
        """Sets the request timeout.

        Args:
            seconds: Timeout in seconds.

        Returns:
            Self for method chaining.
        """
        self._timeout = seconds
        return self

    def max_tokens(self, tokens: int) -> "ProviderBuilder":
        """Sets the maximum token budget per request.

        Args:
            tokens: Token limit integer.

        Returns:
            Self for method chaining.
        """
        self._max_tokens = tokens
        return self

    def temperature(self, temp: float) -> "ProviderBuilder":
        """Sets the sampling temperature.

        Args:
            temp: Float between 0.0 and 2.0.

        Returns:
            Self for method chaining.
        """
        self._temperature = temp
        return self

    def streaming(self, enabled: bool = True) -> "ProviderBuilder":
        """Enables or disables streaming responses.

        Args:
            enabled: Boolean flag.

        Returns:
            Self for method chaining.
        """
        self._streaming = enabled
        return self

    def option(self, key: str, value: Any) -> "ProviderBuilder":
        """Sets a provider-specific option.

        Args:
            key: Option key.
            value: Option value.

        Returns:
            Self for method chaining.
        """
        self._options[key] = value
        return self

    def build(self) -> ProviderConfig:
        """Constructs the final ProviderConfig.

        Returns:
            Validated ProviderConfig instance.
        """
        return ProviderConfig(
            provider_id=self._provider_id,
            model_id=self._model_id,
            api_key_env=self._api_key_env,
            base_url=self._base_url,
            timeout_seconds=self._timeout,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
            streaming=self._streaming,
            options=dict(self._options),
        )
