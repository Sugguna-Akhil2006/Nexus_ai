"""Provider config helper mapping configurations specific to Gemini, OpenAI, and Ollama."""

from __future__ import annotations

from typing import Dict

from backend.config.models import LLMProviderSetting


class ProviderConfigHelper:
    """Manages active LLM provider configurations."""

    def __init__(self, providers: Dict[str, LLMProviderSetting]) -> None:
        self._providers = providers

    def is_provider_available(self, name: str) -> bool:
        """Returns True if the provider is enabled and configured."""
        p = self._providers.get(name.lower())
        if not p:
            return False
        if not p.enabled:
            return False
        # Ollama doesn't strictly require an API Key to be available
        if name.lower() == "ollama":
            return True
        return len(p.api_key) > 0
