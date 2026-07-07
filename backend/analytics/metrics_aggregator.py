"""Metrics aggregator calculating basic mathematical averages and aggregates."""

from __future__ import annotations

from typing import List

from backend.analytics.models import MetricRecord, MetricType


class MetricsAggregator:
    """Aggregates list values for platform-wide dashboard reports."""

    @staticmethod
    def get_average(records: List[MetricRecord], name: str) -> float:
        """Calculates average value for the matching metric name."""
        matches = [r.value for r in records if r.name == name]
        if not matches:
            return 0.0
        return round(sum(matches) / len(matches), 2)

    @staticmethod
    def get_sum(records: List[MetricRecord], name: str) -> float:
        """Calculates sum value for the matching metric name."""
        return sum(r.value for r in records if r.name == name)

    @staticmethod
    def get_count(records: List[MetricRecord], name: str) -> int:
        """Returns match count for the metric name."""
        return sum(1 for r in records if r.name == name)
