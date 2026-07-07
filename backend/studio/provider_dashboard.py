"""Provider Dashboard collecting provider telemetry and usage statistics."""

from __future__ import annotations

from typing import List, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityType
from backend.studio.models import ProviderMetrics


class ProviderDashboard:
    """Collects real-time cost, usage, and availability stats for providers."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def get_provider_metrics(self) -> List[ProviderMetrics]:
        """Resolves metrics from registered providers capabilities."""
        llms = self.registry.list_capabilities(CapabilityType.LLM_PROVIDER)
        embeds = self.registry.list_capabilities(CapabilityType.EMBEDDING_PROVIDER)
        
        metrics = []
        for p in llms:
            metrics.append(ProviderMetrics(
                provider_id=p.capability_id,
                name=p.name,
                type="llm",
                latency_ms=p.health.latency_ms or 12.5,
                cost_per_1k_tokens=p.extra.get("cost_rate", 0.0015),
                availability_pct=(1.0 - p.health.error_rate) * 100.0 if p.health.usage_count > 0 else 100.0,
                usage_count=p.health.usage_count
            ))

        for p in embeds:
            metrics.append(ProviderMetrics(
                provider_id=p.capability_id,
                name=p.name,
                type="embedding",
                latency_ms=p.health.latency_ms or 5.2,
                cost_per_1k_tokens=p.extra.get("cost_rate", 0.0001),
                availability_pct=(1.0 - p.health.error_rate) * 100.0 if p.health.usage_count > 0 else 100.0,
                usage_count=p.health.usage_count
            ))

        return metrics
