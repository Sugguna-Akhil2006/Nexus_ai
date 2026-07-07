"""Model Router coordinating quality, cost, and latency routing decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import ModelProfile
from backend.platform.model_manager import ModelManager
from backend.platform.provider_manager import ProviderManager
from backend.providers.router.models import InferenceRequest, RouterRecommendation, RouterExecutionStats
from backend.providers.router.routing_policy import RoutingPolicyResolver
from backend.providers.router.capability_matcher import CapabilityMatcher
from backend.providers.router.cost_estimator import CostEstimator
from backend.providers.router.latency_predictor import LatencyPredictor
from backend.providers.router.quality_ranker import QualityRanker
from backend.providers.router.fallback_manager import FallbackManager
from backend.providers.router.provider_selector import ProviderSelector
from backend.providers.router.embedding_selector import EmbeddingSelector


class ModelRouter:
    """Orchestrates model selection routing flow across available providers."""

    def __init__(
        self,
        model_mgr: Optional[ModelManager] = None,
        provider_mgr: Optional[ProviderManager] = None
    ) -> None:
        self.model_mgr = model_mgr or ModelManager()
        self.provider_mgr = provider_mgr or ProviderManager()
        self.policy_resolver = RoutingPolicyResolver()
        self.capability_matcher = CapabilityMatcher()
        self.cost_estimator = CostEstimator()
        self.latency_predictor = LatencyPredictor()
        self.quality_ranker = QualityRanker()
        self.fallback_manager = FallbackManager()
        self.provider_selector = ProviderSelector()
        self.embedding_selector = EmbeddingSelector()
        
        self._event_bus = EventBus()

    def route_request(self, request: InferenceRequest) -> RouterRecommendation:
        """Determines best model route using weighted capabilities and cost/quality priorities."""
        # 1. Publish routing started event
        self._publish_event("routing.started", {"task_type": request.task_type})

        # 2. Get list of active models
        models = self.model_mgr.list_models()
        active_models = [m for m in models if m.is_active]

        # 3. Filter by required capabilities
        eligible = self.capability_matcher.filter_eligible_models(active_models, request.required_capabilities)
        if not eligible:
            # Fallback to default
            default = self.model_mgr.get_default_model()
            eligible = [default] if default else active_models

        # 4. Filter by healthy providers
        healthy = []
        for m in eligible:
            prov = self.provider_mgr.get_provider(m.provider_id)
            if prov and prov.is_active and prov.health_status == "healthy":
                healthy.append(m)

        final_candidates = healthy if healthy else eligible

        # 5. Resolve policy weights
        weights = self.policy_resolver.resolve_weights(request.policy_preference)

        # 6. Select model
        selected = self.provider_selector.select_best_model(final_candidates, weights)

        # 7. Calculate estimates
        cost = self.cost_estimator.estimate_cost(selected.model_id)
        latency = self.latency_predictor.predict_latency_ms(selected.model_id)
        quality = self.quality_ranker.get_quality_score(selected.model_id)

        # 8. Emit provider selected event
        self._publish_event("provider.selected", {"model_id": selected.model_id, "provider_id": selected.provider_id})

        # 9. Emit routing completed
        self._publish_event("routing.completed", {"model_id": selected.model_id})

        return RouterRecommendation(
            model_id=selected.model_id,
            provider_id=selected.provider_id,
            estimated_cost=cost,
            estimated_latency_ms=latency,
            quality_rank=quality
        )

    def report_execution_metrics(self, stats: RouterExecutionStats) -> None:
        """Logs actual metrics back to database for future latency prediction learning."""
        from backend.platform.usage_analytics import UsageAnalytics
        analytics = UsageAnalytics()
        analytics.log_request(
            model_id=stats.model_id,
            provider_id=stats.provider_id,
            tokens=stats.tokens_used,
            cost=stats.actual_cost,
            latency_ms=stats.actual_latency_ms,
            status="success" if stats.is_success else "failed"
        )

    def _publish_event(self, event_name: str, payload: dict) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ModelRouter",
            payload={
                "event": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                **payload
            }
        )
        self._event_bus.publish(event)
