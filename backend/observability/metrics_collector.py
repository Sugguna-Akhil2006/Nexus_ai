"""Accumulates ModelMetrics per provider and model across all executions."""

import threading
from collections import defaultdict
from typing import Any, Dict, List

from backend.observability.models import ModelMetrics


class MetricsCollector:
    """Thread-safe store and aggregator for model invocation metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: List[ModelMetrics] = []
        # provider → model → {count, tokens_in, tokens_out, cost, latency_sum, failures}
        self._agg: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(
            lambda: defaultdict(lambda: {
                "count": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "cost_usd": 0.0,
                "latency_sum_ms": 0.0,
                "failures": 0,
            })
        )

    def record_invocation(self, metrics: ModelMetrics) -> None:
        """Stores a model invocation record and updates aggregations.

        Args:
            metrics: The ``ModelMetrics`` instance to persist.
        """
        with self._lock:
            self._records.append(metrics)
            agg = self._agg[metrics.provider][metrics.model]
            agg["count"] += 1
            agg["tokens_in"] += metrics.tokens_in
            agg["tokens_out"] += metrics.tokens_out
            agg["cost_usd"] += metrics.estimated_cost_usd
            agg["latency_sum_ms"] += metrics.latency_ms
            if metrics.failed:
                agg["failures"] += 1

    def get_provider_stats(self) -> Dict[str, Any]:
        """Returns aggregated statistics grouped by provider and model.

        Returns:
            Nested dict: ``provider → model → stats``.
        """
        with self._lock:
            result: Dict[str, Any] = {}
            for provider, models in self._agg.items():
                result[provider] = {}
                for model, stats in models.items():
                    count = max(stats["count"], 1)
                    result[provider][model] = {
                        "invocations": stats["count"],
                        "tokens_in": stats["tokens_in"],
                        "tokens_out": stats["tokens_out"],
                        "total_cost_usd": round(stats["cost_usd"], 6),
                        "avg_latency_ms": round(stats["latency_sum_ms"] / count, 3),
                        "failures": stats["failures"],
                        "failure_rate": round(stats["failures"] / count, 4),
                    }
            return result

    def get_total_cost(self) -> float:
        """Returns the accumulated estimated cost across all invocations (USD)."""
        with self._lock:
            return round(sum(r.estimated_cost_usd for r in self._records), 6)

    def list_all(self) -> List[ModelMetrics]:
        """Returns all raw invocation records."""
        with self._lock:
            return list(self._records)
