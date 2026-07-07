"""Thread-safe background job lifecycle manager for the Product Experience Layer.

Provides a singleton ProgressTracker that manages the full lifecycle of
background jobs: QUEUED → RUNNING → COMPLETED | FAILED | CANCELLED,
with retry support, estimated completion calculation, and stage-level detail.

This tracker is independent of the per-service caches used by
GitHubProductService and ResumeProductService, ensuring zero coupling with
the existing AI service layer.

Example usage::

    tracker = ProgressTracker()
    job_id = tracker.create_job(job_type="resume_export", label="Export Resume")
    tracker.update_job(job_id, progress_pct=50, stage="Rendering HTML")
    tracker.complete_job(job_id, result={"file": "report.html"})
    job = tracker.get_job(job_id)
"""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Lifecycle states for a tracked background job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRecord(BaseModel):
    """Complete state snapshot for a single tracked job.

    Attributes:
        job_id: Unique identifier for the job.
        job_type: Domain type label (e.g. 'resume_export', 'github_analysis').
        label: Human-readable display name.
        status: Current lifecycle state.
        progress_pct: Completion percentage (0–100).
        stage: Current pipeline stage description.
        message: Status message or error description.
        created_at: UTC timestamp when the job was created.
        started_at: UTC timestamp when execution began.
        completed_at: UTC timestamp when the job finished.
        estimated_completion: Estimated UTC finish timestamp.
        retry_count: Number of retry attempts so far.
        max_retries: Maximum allowed retries before permanent failure.
        result: Payload attached on completion.
        error: Error detail attached on failure.
        metadata: Arbitrary context metadata.
    """

    job_id: str
    job_type: str
    label: str
    status: JobStatus = JobStatus.QUEUED
    progress_pct: int = 0
    stage: str = "Queued"
    message: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_terminal(self) -> bool:
        """Returns True when the job is in a non-recoverable terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)

    def duration_seconds(self) -> Optional[float]:
        """Returns elapsed wall-clock seconds since job start, or None if not started."""
        if self.started_at is None:
            return None
        end = self.completed_at or datetime.now(timezone.utc)
        return (end - self.started_at).total_seconds()


class ProgressTracker:
    """Singleton thread-safe background job registry for the product layer.

    Maintains an in-memory registry of JobRecord instances, providing full
    CRUD and lifecycle management. All methods are safe for concurrent use.
    """

    _instance: Optional["ProgressTracker"] = None
    _class_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "ProgressTracker":
        with cls._class_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._jobs: Dict[str, JobRecord] = {}
                instance._lock = threading.RLock()
                cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Job Creation
    # ------------------------------------------------------------------

    def create_job(
        self,
        job_type: str,
        label: str,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Creates a new job and returns its unique ID.

        Args:
            job_type: Domain type label for the job.
            label: Human-readable display name.
            max_retries: Maximum retry attempts allowed.
            metadata: Optional key-value metadata to attach.

        Returns:
            Unique job ID string.
        """
        job_id = f"pjob-{str(uuid.uuid4())[:12]}"
        record = JobRecord(
            job_id=job_id,
            job_type=job_type,
            label=label,
            max_retries=max_retries,
            metadata=metadata or {},
        )
        with self._lock:
            self._jobs[job_id] = record
        return job_id

    # ------------------------------------------------------------------
    # Lifecycle Transitions
    # ------------------------------------------------------------------

    def start_job(self, job_id: str, stage: str = "Initializing") -> bool:
        """Transitions a QUEUED job to RUNNING.

        Args:
            job_id: Target job identifier.
            stage: Initial pipeline stage description.

        Returns:
            True on success, False if the job was not found or not QUEUED.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status != JobStatus.QUEUED:
                return False
            record.status = JobStatus.RUNNING
            record.started_at = datetime.now(timezone.utc)
            record.stage = stage
            return True

    def update_job(
        self,
        job_id: str,
        progress_pct: Optional[int] = None,
        stage: Optional[str] = None,
        message: Optional[str] = None,
        estimated_completion: Optional[datetime] = None,
    ) -> bool:
        """Updates progress and stage information for a RUNNING job.

        Args:
            job_id: Target job identifier.
            progress_pct: New completion percentage (0–100).
            stage: Updated pipeline stage description.
            message: Updated status message.
            estimated_completion: Revised estimated finish timestamp.

        Returns:
            True on success, False if the job was not found or not RUNNING.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status != JobStatus.RUNNING:
                return False
            if progress_pct is not None:
                record.progress_pct = max(0, min(100, progress_pct))
            if stage is not None:
                record.stage = stage
            if message is not None:
                record.message = message
            if estimated_completion is not None:
                record.estimated_completion = estimated_completion
            return True

    def complete_job(
        self,
        job_id: str,
        result: Optional[Any] = None,
        message: str = "Completed successfully",
    ) -> bool:
        """Transitions a RUNNING job to COMPLETED.

        Args:
            job_id: Target job identifier.
            result: Payload to attach (e.g. report dict, file path).
            message: Completion message.

        Returns:
            True on success, False if not found or not RUNNING.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status != JobStatus.RUNNING:
                return False
            record.status = JobStatus.COMPLETED
            record.progress_pct = 100
            record.stage = "Completed"
            record.message = message
            record.completed_at = datetime.now(timezone.utc)
            record.result = result
            return True

    def fail_job(self, job_id: str, error: str) -> bool:
        """Transitions a RUNNING job to FAILED.

        Args:
            job_id: Target job identifier.
            error: Error description string.

        Returns:
            True on success, False if not found or not RUNNING.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status != JobStatus.RUNNING:
                return False
            record.status = JobStatus.FAILED
            record.stage = "Failed"
            record.message = error
            record.error = error
            record.completed_at = datetime.now(timezone.utc)
            return True

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a QUEUED or RUNNING job.

        Args:
            job_id: Target job identifier.

        Returns:
            True on success, False if not found or already terminal.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.is_terminal():
                return False
            record.status = JobStatus.CANCELLED
            record.stage = "Cancelled"
            record.message = "Job cancelled by user"
            record.completed_at = datetime.now(timezone.utc)
            return True

    def retry_job(self, job_id: str) -> bool:
        """Resets a FAILED job to QUEUED for re-execution.

        Args:
            job_id: Target job identifier.

        Returns:
            True on success, False if not found, not FAILED, or max retries exceeded.
        """
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record.status != JobStatus.FAILED:
                return False
            if record.retry_count >= record.max_retries:
                return False
            record.retry_count += 1
            record.status = JobStatus.QUEUED
            record.stage = f"Retry #{record.retry_count}"
            record.message = "Retrying…"
            record.error = None
            record.started_at = None
            record.completed_at = None
            record.progress_pct = 0
            return True

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        """Retrieves a single job record by ID.

        Args:
            job_id: Target job identifier.

        Returns:
            JobRecord if found, else None.
        """
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[JobRecord]:
        """Lists tracked jobs with optional filtering.

        Args:
            status: Filter by lifecycle state.
            job_type: Filter by job type label.
            limit: Maximum number of records to return (newest first).

        Returns:
            List of matching JobRecord instances, sorted newest-first.
        """
        with self._lock:
            records = list(self._jobs.values())

        # Apply filters
        if status is not None:
            records = [r for r in records if r.status == status]
        if job_type is not None:
            records = [r for r in records if r.job_type == job_type]

        # Sort newest-first by creation time
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[:limit]

    def purge_terminal(self, older_than_seconds: int = 3600) -> int:
        """Removes completed/failed/cancelled jobs older than a threshold.

        Args:
            older_than_seconds: Age threshold in seconds.

        Returns:
            Number of purged records.
        """
        cutoff = time.time() - older_than_seconds
        with self._lock:
            to_purge = [
                jid
                for jid, r in self._jobs.items()
                if r.is_terminal()
                and r.completed_at is not None
                and r.completed_at.timestamp() < cutoff
            ]
            for jid in to_purge:
                del self._jobs[jid]
        return len(to_purge)

    def summary(self) -> Dict[str, int]:
        """Returns count of jobs per status.

        Returns:
            Dict mapping each JobStatus value to its count.
        """
        with self._lock:
            counts: Dict[str, int] = {s.value: 0 for s in JobStatus}
            for record in self._jobs.values():
                counts[record.status.value] += 1
            return counts
