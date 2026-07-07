"""Trend analyzer evaluating daily and weekly traffic shifts."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from backend.analytics.models import MetricRecord


class TrendAnalyzer:
    """Evaluates metrics shifts over time intervals."""

    @staticmethod
    def calculate(records: List[MetricRecord]) -> Dict[str, Any]:
        """Calculates metric value spikes or trends over captured timestamps."""
        history = defaultdict(list)
        for r in records:
            day = r.timestamp.split("T")[0]
            history[day].append(r.value)

        trends = {}
        for day, vals in history.items():
            trends[day] = {
                "count": len(vals),
                "avg_val": round(sum(vals) / len(vals), 2) if vals else 0.0,
            }

        return {
            "daily_trends": trends,
        }
