"""Performance dashboard compiling CPU, memory, and duration statistics."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.diagnostics.metrics_collector import MetricsCollector


class PerformanceDashboard:
    """Aggregates workflow latency trends, system metrics, and memory bounds."""

    @staticmethod
    def get_dashboard_data(
        traces: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compiles request logs and hardware metrics into a performance summary.

        Args:
            traces: List of serialized RequestTrace dicts.

        Returns:
            Snapshot dictionary containing system stats and averages.
        """
        n_traces = len(traces)
        avg_duration = 0.0
        max_duration = 0.0

        if n_traces > 0:
            total_dur = sum(t["duration_ms"] for t in traces)
            avg_duration = total_dur / n_traces
            max_duration = max(t["duration_ms"] for t in traces)

        # Retrieve system usage statistics
        sys_metrics = MetricsCollector.measure_resource_usage()

        return {
            "total_requests": n_traces,
            "avg_workflow_duration_ms": round(avg_duration, 2),
            "max_workflow_duration_ms": round(max_duration, 2),
            "cpu_process_time_sec": sys_metrics.get("cpu_time_sec", 0.0),
            "memory_usage_bytes": sys_metrics.get("memory_bytes", 0),
            "peak_memory_bytes": sys_metrics.get("peak_memory_bytes", 0),
            "status": "healthy",
        }
