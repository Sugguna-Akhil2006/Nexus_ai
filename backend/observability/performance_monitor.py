"""Collects per-module latency samples and publishes threshold breach events."""

import threading
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.observability.models import PerformanceSnapshot


class PerformanceMonitor:
    """Records module latencies and surfaces performance threshold violations.

    When a recorded latency exceeds ``threshold_ms``, the monitor publishes a
    ``performance.threshold.exceeded`` event on the EventBus.
    """

    def __init__(self, threshold_ms: float = 5000.0) -> None:
        self._lock = threading.Lock()
        self._threshold_ms = threshold_ms
        self._event_bus = EventBus()
        # module → [latency_ms, ...]
        self._samples: Dict[str, List[float]] = defaultdict(list)
        self._concurrent_requests: int = 0
        self._cache_hits: int = 0
        self._cache_total: int = 0

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_latency(self, module: str, latency_ms: float) -> None:
        """Records a latency sample for a module and checks threshold.

        Args:
            module: The intelligence module or component name.
            latency_ms: Observed latency in milliseconds.
        """
        with self._lock:
            self._samples[module].append(latency_ms)

        if latency_ms > self._threshold_ms:
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="PerformanceMonitor",
                payload={
                    "event": "performance.threshold.exceeded",
                    "module": module,
                    "latency_ms": latency_ms,
                    "threshold_ms": self._threshold_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ))

    def increment_concurrent(self) -> None:
        """Signals that a new concurrent request has started."""
        with self._lock:
            self._concurrent_requests += 1

    def decrement_concurrent(self) -> None:
        """Signals that a concurrent request has completed."""
        with self._lock:
            self._concurrent_requests = max(0, self._concurrent_requests - 1)

    def record_cache_result(self, hit: bool) -> None:
        """Records a cache lookup outcome for hit-rate calculation."""
        with self._lock:
            self._cache_total += 1
            if hit:
                self._cache_hits += 1

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_avg_latency(self, module: Optional[str] = None) -> float:
        """Returns the average latency in ms for a module or across all modules."""
        with self._lock:
            if module:
                samples = self._samples.get(module, [])
                return round(sum(samples) / len(samples), 3) if samples else 0.0
            all_samples = [v for lst in self._samples.values() for v in lst]
            return round(sum(all_samples) / len(all_samples), 3) if all_samples else 0.0

    def get_slowest_ops(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Returns the top-N slowest module operations recorded."""
        with self._lock:
            all_ops = [
                {"module": mod, "latency_ms": lat}
                for mod, samples in self._samples.items()
                for lat in samples
            ]
        all_ops.sort(key=lambda x: x["latency_ms"], reverse=True)
        return all_ops[:top_n]

    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """Returns a complete performance snapshot at the current moment."""
        with self._lock:
            module_timings = {
                mod: round(sum(s) / len(s), 3)
                for mod, s in self._samples.items()
                if s
            }
            cache_rate = (
                round(self._cache_hits / self._cache_total, 4) if self._cache_total else 0.0
            )
            concurrent = self._concurrent_requests

        all_latencies = [lat for lst in self._samples.values() for lat in lst]
        avg = round(sum(all_latencies) / len(all_latencies), 3) if all_latencies else 0.0

        return PerformanceSnapshot(
            avg_latency_ms=avg,
            module_timings=module_timings,
            slowest_operations=self.get_slowest_ops(),
            cache_hit_rate=cache_rate,
            concurrent_requests=concurrent,
        )
