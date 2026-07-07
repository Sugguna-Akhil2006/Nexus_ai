"""Metrics collector measuring execution durations, CPU times, memory bounds, and streaming latencies."""

from __future__ import annotations

import time
import os
from typing import Any, Dict


class MetricsCollector:
    """Utility to collect system utilization metrics and execution performance snaps."""

    @staticmethod
    def measure_resource_usage() -> Dict[str, Any]:
        """Collects current resident memory and system load statistics.

        Returns:
            Dict containing cpu_time_sec, memory_bytes, and peak_memory_bytes.
        """
        import tracemalloc

        # Peak memory tracked via tracemalloc if active
        traced = tracemalloc.get_traced_memory()
        peak_bytes = traced[1] if traced[0] > 0 or traced[1] > 0 else 0

        # Memory usage via system check or mock fallback
        try:
            import psutil
            process = psutil.Process(os.getpid())
            mem_bytes = process.memory_info().rss
        except Exception:
            mem_bytes = 0

        return {
            "cpu_time_sec": round(time.process_time(), 4),
            "memory_bytes": mem_bytes,
            "peak_memory_bytes": peak_bytes,
        }
