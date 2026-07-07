"""Cost dashboard calculator reporting accumulated budget usage."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.analytics.models import MetricRecord, MetricType


class CostDashboard:
    """Consolidates cost and resource metrics to feed console dashboards."""

    @staticmethod
    def calculate(records: List[MetricRecord]) -> Dict[str, Any]:
        """Collects cost sums and flags if they exceed pre-set warning limits."""
        provs = [r for r in records if r.metric_type == MetricType.PROVIDER]
        cost_sum = sum(r.value for r in provs if r.name == "provider_cost_usd")

        return {
            "total_usd": round(cost_sum, 6),
            "budget_limit_usd": 100.0,
            "pct_consumed": round((cost_sum / 100.0) * 100, 2) if cost_sum else 0.0,
            "warning": cost_sum > 80.0,
        }
