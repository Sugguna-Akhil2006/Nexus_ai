"""Provider analytics calculator aggregating model latencies, costs, and tokens."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.analytics.models import MetricRecord, MetricType


class ProviderAnalytics:
    """Calculates LLM provider usage cost and tokens volume totals."""

    @staticmethod
    def calculate(records: List[MetricRecord]) -> Dict[str, Any]:
        """Aggregates cost summaries, latency metrics, and token usage."""
        provs = [r for r in records if r.metric_type == MetricType.PROVIDER]

        total_cost = sum(r.value for r in provs if r.name == "provider_cost_usd")
        tokens = sum(r.value for r in provs if r.name == "provider_tokens")

        latencies = [r.value for r in provs if r.name == "provider_latency_ms"]
        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0

        return {
            "total_cost_usd": round(total_cost, 6),
            "total_tokens_consumed": int(tokens),
            "avg_latency_ms": avg_latency,
        }
