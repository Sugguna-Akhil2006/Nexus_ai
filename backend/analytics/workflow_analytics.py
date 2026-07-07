"""Workflow analytics calculator tracking workflow executions and execution details."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.analytics.models import MetricRecord, MetricType


class WorkflowAnalytics:
    """Calculates aggregates related to workflow runs, durations, and rates."""

    @staticmethod
    def calculate(records: List[MetricRecord]) -> Dict[str, Any]:
        """Calculates workflow success rates, average duration, and failure frequencies."""
        wfs = [r for r in records if r.metric_type == MetricType.WORKFLOW]

        runs = sum(1 for r in wfs if r.name == "workflow_run")
        successes = sum(1 for r in wfs if r.name == "workflow_run" and r.context.get("status") == "success")
        failures = sum(1 for r in wfs if r.name == "workflow_run" and r.context.get("status") == "failure")

        durations = [r.value for r in wfs if r.name == "workflow_duration_ms"]
        avg_dur = round(sum(durations) / len(durations), 2) if durations else 0.0

        success_rate = round(successes / runs, 4) if runs else 1.0

        return {
            "total_runs": runs,
            "success_rate": success_rate,
            "failure_rate": round(failures / runs, 4) if runs else 0.0,
            "avg_duration_ms": avg_dur,
        }
