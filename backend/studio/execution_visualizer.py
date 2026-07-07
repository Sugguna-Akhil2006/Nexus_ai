"""Execution Visualizer constructing runtime execution timeline charts and relationships."""

from __future__ import annotations

from typing import Any, Dict, List


class ExecutionVisualizer:
    """Builds interactive runtime metrics and Gantt execution charts data."""

    def compile_execution_timeline(self, execution_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts raw database audit logs to displayable execution nodes with offset times."""
        timeline = []
        base_time = 0.0

        for idx, entry in enumerate(execution_history):
            latency = entry.get("latency_ms", 100.0)
            timeline.append({
                "id": entry.get("execution_id") or f"step-{idx}",
                "name": entry.get("module_used") or "Workflow Step",
                "status": entry.get("status") or "completed",
                "start_offset_ms": base_time,
                "duration_ms": latency,
                "end_offset_ms": base_time + latency
            })
            base_time += latency

        return timeline
