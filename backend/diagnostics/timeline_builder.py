"""Timeline builder compiling sequential and concurrent execution events into visual step hierarchies."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.diagnostics.models import TimelineStep


class TimelineBuilder:
    """Helper class to construct and format lists of TimelineSteps for request traces."""

    def __init__(self) -> None:
        self._steps: List[TimelineStep] = []

    def record_start(
        self,
        name: str,
        step_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends a new running/pending step to the timeline."""
        step = TimelineStep(
            step_name=name,
            step_type=step_type,
            status="running",
            metadata=metadata or {},
        )
        self._steps.append(step)

    def record_completion(
        self,
        name: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Marks an existing step as completed with the measured duration."""
        for step in self._steps:
            if step.step_name == name and step.status == "running":
                step.status = "completed"
                step.duration_ms = round(duration_ms, 2)
                if metadata:
                    step.metadata.update(metadata)
                return

    def record_failure(
        self,
        name: str,
        error_msg: str,
        duration_ms: float,
    ) -> None:
        """Marks a step as failed with the error message logged in metadata."""
        for step in self._steps:
            if step.step_name == name and step.status == "running":
                step.status = "failed"
                step.duration_ms = round(duration_ms, 2)
                step.metadata["error"] = error_msg
                return

    def get_steps(self) -> List[TimelineStep]:
        """Returns the gathered list of steps."""
        return list(self._steps)
