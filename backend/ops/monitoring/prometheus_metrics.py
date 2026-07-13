"""Prometheus metrics exporter returning standard formatted metrics."""

import threading
from typing import Dict, Any


class PrometheusMetrics:
    """Manages counters and outputs them in Prometheus text format."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._counters: Dict[str, float] = {
            "http_requests_total": 0.0,
            "http_failures_total": 0.0,
            "db_queries_total": 0.0,
            "redis_hits_total": 0.0,
            "backup_runs_total": 0.0,
            "backup_failures_total": 0.0
        }
        self._lock = threading.Lock()
        self._initialized = True

    def increment(self, name: str, amount: float = 1.0) -> None:
        """Increments a counter.

        Args:
            name: Metric counter name.
            amount: Value to increment by.
        """
        with self._lock:
            if name in self._counters:
                self._counters[name] += amount

    def get_metrics_text(self) -> str:
        """Formats and outputs scrapable prometheus metrics block."""
        lines = []
        with self._lock:
            for name, val in self._counters.items():
                lines.append(f"# HELP {name} Counter metric for {name.replace('_', ' ')}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {val}")
        return "\n".join(lines) + "\n"
        
    def clear(self) -> None:
        """Resets all metrics counters."""
        with self._lock:
            for key in self._counters:
                self._counters[key] = 0.0
