"""Metrics collector to capture system performance, database operations, queues, and API usage."""

import threading
from typing import Dict, Any


class MetricsCollector:
    """Thread-safe collector for key application and system operational metrics."""

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
        from datetime import datetime, timedelta
        self._metrics: Dict[str, Any] = {
            "api_requests_total": 0,
            "api_requests_by_endpoint": {},
            "api_failures_total": 0,
            "db_queries_total": 0,
            "db_query_errors": 0,
            "storage_uploads_total": 0,
            "storage_downloads_total": 0,
            "queue_jobs_submitted": 0,
            "queue_jobs_failed": 0,
            "usage_timeline": self._generate_initial_timeline()
        }
        self._lock = threading.Lock()
        self._initialized = True

    def _generate_initial_timeline(self) -> list:
        from datetime import datetime, timedelta
        timeline = []
        now = datetime.utcnow()
        for i in range(6, -1, -1):
            t = now - timedelta(hours=i)
            time_str = t.strftime("%H:00")
            timeline.append({
                "time": time_str,
                "requests": 0,
                "failures": 0,
                "data_kb": 0.0
            })
        return timeline

    def increment(self, name: str, amount: int = 1) -> None:
        """Increments a counter metric.

        Args:
            name: Metric counter name.
            amount: Value to add.
        """
        with self._lock:
            if name in self._metrics:
                self._metrics[name] += amount

    def increment_endpoint(self, endpoint: str) -> None:
        """Tracks requests counts per individual route path."""
        self.record_request(endpoint)

    def record_request(self, endpoint: str, data_size_bytes: int = 0, is_failure: bool = False) -> None:
        from datetime import datetime
        with self._lock:
            self._metrics["api_requests_total"] += 1
            by_route = self._metrics["api_requests_by_endpoint"]
            by_route[endpoint] = by_route.get(endpoint, 0) + 1
            
            if is_failure:
                self._metrics["api_failures_total"] += 1

            now_hour = datetime.utcnow().strftime("%H:00")
            timeline = self._metrics["usage_timeline"]
            
            found = False
            for slot in timeline:
                if slot["time"] == now_hour:
                    slot["requests"] += 1
                    slot["data_kb"] += round(data_size_bytes / 1024.0, 2)
                    if is_failure:
                        slot["failures"] += 1
                    found = True
                    break
            
            if not found:
                timeline.append({
                    "time": now_hour,
                    "requests": 1,
                    "failures": 1 if is_failure else 0,
                    "data_kb": round(data_size_bytes / 1024.0, 2)
                })
                if len(timeline) > 7:
                    timeline.pop(0)

    def get_all_metrics(self) -> Dict[str, Any]:
        """Returns snapshot copy of all tracked counters."""
        with self._lock:
            return dict(self._metrics)
            
    def clear(self) -> None:
        """Clears/resets all metrics counters."""
        with self._lock:
            self._metrics["api_requests_total"] = 0
            self._metrics["api_requests_by_endpoint"].clear()
            self._metrics["api_failures_total"] = 0
            self._metrics["db_queries_total"] = 0
            self._metrics["db_query_errors"] = 0
            self._metrics["storage_uploads_total"] = 0
            self._metrics["storage_downloads_total"] = 0
            self._metrics["queue_jobs_submitted"] = 0
            self._metrics["queue_jobs_failed"] = 0
            self._metrics["usage_timeline"] = self._generate_initial_timeline()
