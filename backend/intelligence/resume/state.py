"""Thread-safe Pipeline State Management for Resume Intelligence workflows."""

import threading
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, PrivateAttr


class WorkflowState(BaseModel):
    """Tracks state and execution telemetry for the resume analysis pipeline."""
    current_stage: str = "started"
    completed_stages: List[str] = Field(default_factory=list)
    failed_stage: Optional[str] = None
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    execution_times: Dict[str, float] = Field(default_factory=dict)
    pipeline_status: str = "started"  # started, running, completed, failed
    errors: Dict[str, str] = Field(default_factory=dict)

    # Thread-safety lock
    _lock: threading.RLock = PrivateAttr(default_factory=threading.RLock)

    def start_stage(self, stage_name: str) -> None:
        """Updates current stage and marks pipeline status to running."""
        with self._lock:
            self.current_stage = stage_name
            self.pipeline_status = "running"

    def complete_stage(self, stage_name: str, duration: float) -> None:
        """Records stage completion and its execution timing."""
        with self._lock:
            if stage_name not in self.completed_stages:
                self.completed_stages.append(stage_name)
            self.execution_times[stage_name] = round(duration, 4)

    def fail_stage(self, stage_name: str, error_msg: str) -> None:
        """Records a failed stage and sets the failed status flag."""
        with self._lock:
            self.failed_stage = stage_name
            self.errors[stage_name] = error_msg
            self.pipeline_status = "failed"

    def record_retry(self, stage_name: str) -> None:
        """Increments the retry counter for a target workflow stage."""
        with self._lock:
            self.retry_counts[stage_name] = self.retry_counts.get(stage_name, 0) + 1
