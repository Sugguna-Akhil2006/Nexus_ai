"""Thread-safe state manager for modular intelligence executions."""

import threading
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, PrivateAttr


class ExecutionState(BaseModel):
    """Tracks running status, retry counts, timing metrics, and warnings across modules."""
    status: str = "started"  # started, running, completed, failed, cancelled, partial_success
    current_stage: Optional[str] = None
    completed_stages: List[str] = Field(default_factory=list)
    failed_stages: List[str] = Field(default_factory=list)
    retry_counts: Dict[str, int] = Field(default_factory=dict)
    execution_times: Dict[str, float] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    warnings: Dict[str, List[str]] = Field(default_factory=dict)

    _lock: threading.RLock = PrivateAttr(default_factory=threading.RLock)

    def start_stage(self, stage_name: str) -> None:
        """Sets the current running stage."""
        with self._lock:
            self.current_stage = stage_name
            self.status = "running"

    def complete_stage(self, stage_name: str, duration: float) -> None:
        """Appends a completed stage and logs its execution duration."""
        with self._lock:
            if stage_name not in self.completed_stages:
                self.completed_stages.append(stage_name)
            self.execution_times[stage_name] = round(duration, 4)

    def fail_stage(self, stage_name: str, error_msg: str) -> None:
        """Records a failed stage and its error log."""
        with self._lock:
            if stage_name not in self.failed_stages:
                self.failed_stages.append(stage_name)
            self.errors[stage_name] = error_msg
            self.status = "partial_success" if self.completed_stages else "failed"

    def record_retry(self, stage_name: str) -> None:
        """Increments stage execution retry count."""
        with self._lock:
            self.retry_counts[stage_name] = self.retry_counts.get(stage_name, 0) + 1

    def add_warning(self, stage_name: str, warning_msg: str) -> None:
        """Appends execution warning logs for diagnostics."""
        with self._lock:
            if stage_name not in self.warnings:
                self.warnings[stage_name] = []
            self.warnings[stage_name].append(warning_msg)
