"""Collects and summarises per-execution timing and step outcome metrics."""

import threading
from datetime import datetime
from typing import Any, Dict, List


class WorkflowMetrics:
    """Accumulates step-level and execution-level performance measurements."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: List[Dict[str, Any]] = []

    def record_step_completion(
        self,
        execution_id: str,
        step_id: str,
        step_name: str,
        status: str,
        duration_seconds: float,
    ) -> None:
        """Appends a step-level timing record."""
        with self._lock:
            self._records.append({
                "type": "step",
                "execution_id": execution_id,
                "step_id": step_id,
                "step_name": step_name,
                "status": status,
                "duration_seconds": duration_seconds,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def record_execution_result(
        self,
        execution_id: str,
        workflow_id: str,
        status: str,
        duration_seconds: float,
        step_count: int,
    ) -> None:
        """Appends a workflow-level outcome record."""
        with self._lock:
            self._records.append({
                "type": "execution",
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "status": status,
                "duration_seconds": duration_seconds,
                "step_count": step_count,
                "timestamp": datetime.utcnow().isoformat(),
            })

    def get_summary(self) -> Dict[str, Any]:
        """Returns aggregated statistics across all recorded events."""
        with self._lock:
            executions = [r for r in self._records if r["type"] == "execution"]
            steps = [r for r in self._records if r["type"] == "step"]
            total = len(executions)
            succeeded = sum(1 for e in executions if e["status"] == "COMPLETED")
            failed = sum(1 for e in executions if e["status"] == "FAILED")
            avg_duration = (
                sum(e["duration_seconds"] for e in executions) / total if total else 0.0
            )
            return {
                "total_executions": total,
                "succeeded": succeeded,
                "failed": failed,
                "avg_duration_seconds": round(avg_duration, 3),
                "total_steps_recorded": len(steps),
            }
