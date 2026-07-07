"""Failover Manager detecting model provider outages and rerouting queries."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ProviderProfile, ModelProfile
from backend.platform.provider_manager import ProviderManager
from backend.platform.model_manager import ModelManager


class FailoverManager:
    """Manages active LLM provider failures and routes requests to fallback servers."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None, model_mgr: Optional[ModelManager] = None) -> None:
        self.provider_mgr = provider_mgr or ProviderManager()
        self.model_mgr = model_mgr or ModelManager()
        self._event_bus = EventBus()
        self._fallbacks: Dict[str, str] = {
            "openai": "gemini",
            "anthropic": "gemini",
            "gemini": "ollama",
            "ollama": "openai"
        }

    def trigger_provider_failure(self, provider_id: str) -> Optional[str]:
        """Flags provider as degraded, publishes failures, and returns fallback provider ID.

        Args:
            provider_id: Failing provider ID.

        Returns:
            Optional[str]: Target fallback provider ID.
        """
        provider = self.provider_mgr.get_provider(provider_id)
        if not provider:
            return None

        # 1. Update provider status in DB
        provider.health_status = "degraded"
        provider.error_rate = 1.0
        self.provider_mgr.register_provider(provider)

        # 2. Emit provider failed event
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="FailoverManager",
            payload={"event": "provider.failed", "provider_id": provider_id}
        ))

        # 3. Resolve fallback provider
        fallback_id = self._fallbacks.get(provider_id)
        if fallback_id:
            # Emit failover completed event
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="FailoverManager",
                payload={
                    "event": "failover.completed",
                    "failed_provider_id": provider_id,
                    "target_provider_id": fallback_id
                }
            ))
            return fallback_id

        return None
