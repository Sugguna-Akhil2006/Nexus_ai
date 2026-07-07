"""Fallback Manager routing failed requests to backup models."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ModelProfile


class FallbackManager:
    """Cascade failover manager returning secondary backup options."""

    def __init__(self) -> None:
        self._event_bus = EventBus()
        # provider -> backup provider
        self._provider_backups: Dict[str, str] = {
            "openai": "gemini",
            "anthropic": "gemini",
            "gemini": "ollama",
            "ollama": "openai"
        }

    def resolve_fallback(self, failed_model: ModelProfile, active_models: List[ModelProfile]) -> Optional[ModelProfile]:
        """Resolves backup model from list of active models."""
        failed_provider = failed_model.provider_id
        target_provider = self._provider_backups.get(failed_provider, "ollama")

        # Emit fallback event
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="FallbackManager",
            payload={
                "event": "fallback.triggered",
                "failed_model_id": failed_model.model_id,
                "fallback_provider_id": target_provider
            }
        ))

        # Find any active model on target provider
        for m in active_models:
            if m.provider_id == target_provider and m.model_id != failed_model.model_id:
                return m

        # Default to local model if available
        for m in active_models:
            if m.provider_id == "ollama":
                return m

        return None
