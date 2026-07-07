"""Routing Engine directing tasks to LLM models dynamically."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ModelProfile
from backend.platform.provider_manager import ProviderManager
from backend.platform.model_manager import ModelManager


class RoutingEngine:
    """Intelligently routes LLM requests to models based on health, cost, and latency."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None, model_mgr: Optional[ModelManager] = None) -> None:
        self.provider_mgr = provider_mgr or ProviderManager()
        self.model_mgr = model_mgr or ModelManager()
        self._event_bus = EventBus()

    def select_route(self, task_type: str, workspace_id: str, cost_weight: float = 0.5) -> ModelProfile:
        """Selects optimal model route.

        Args:
            task_type: Target capability keyword (e.g. "chat", "extraction").
            workspace_id: User workspace.
            cost_weight: Cost priority (0.0 = prioritize latency, 1.0 = prioritize low cost).

        Returns:
            ModelProfile: Selected optimal model profile.
        """
        models = self.model_mgr.list_models()
        active_models = [m for m in models if m.is_active]
        
        # Filter models by task capability
        eligible_models = [m for m in active_models if task_type in m.capabilities]
        if not eligible_models:
            # Fallback to default
            default_model = self.model_mgr.get_default_model()
            if default_model and default_model.is_active:
                return default_model
            # Fallback to any active model
            if active_models:
                return active_models[0]
            raise RuntimeError("No active models registered in platform operations center.")

        # Check provider health
        healthy_models = []
        for m in eligible_models:
            provider = self.provider_mgr.get_provider(m.provider_id)
            if provider and provider.is_active and provider.health_status == "healthy":
                healthy_models.append(m)

        final_candidates = healthy_models if healthy_models else eligible_models

        # Select low cost model if cost weighted, else select default or first candidate
        if cost_weight > 0.7:
            # Sort by low cost (local models are cheapest, e.g. phi3)
            final_candidates.sort(key=lambda x: 0.0 if x.provider_id == "ollama" else 0.002)

        # Emit routing changed event
        selected = final_candidates[0]
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="RoutingEngine",
            payload={"event": "routing.changed", "workspace_id": workspace_id, "selected_model_id": selected.model_id}
        ))

        return selected
