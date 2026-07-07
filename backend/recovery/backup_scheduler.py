"""Backup scheduler triggering automatic periodic snapshots."""

from __future__ import annotations

import threading
import time
from typing import Callable, List, Optional

from backend.recovery.models import BackupRecord, BackupType


# Callback type: invoked when a scheduled backup fires
BackupCallback = Callable[[BackupType], BackupRecord]


class ScheduledJob:
    """Descriptor for a recurring backup schedule."""

    def __init__(self, job_id: str, backup_type: BackupType, interval_seconds: float) -> None:
        self.job_id = job_id
        self.backup_type = backup_type
        self.interval_seconds = interval_seconds
        self.enabled: bool = True
        self.last_run: Optional[float] = None
        self.run_count: int = 0


class BackupScheduler:
    """Manages recurring backup jobs that fire at configurable intervals.

    Jobs are evaluated by a background daemon thread.  Each job triggers
    the registered callback (typically :meth:`SnapshotManager.take_full_backup`
    or similar) when its interval has elapsed.

    The scheduler stops cleanly when :meth:`stop` is called.

    Example::

        scheduler = BackupScheduler(callback=snapshot_mgr.take_full_backup)
        scheduler.add_job("hourly_full", BackupType.FULL, 3600)
        scheduler.start()
        ...
        scheduler.stop()
    """

    def __init__(self, callback: BackupCallback) -> None:
        self._callback = callback
        self._jobs: List[ScheduledJob] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def add_job(
        self, job_id: str, backup_type: BackupType, interval_seconds: float
    ) -> ScheduledJob:
        """Registers a recurring backup job.

        Args:
            job_id: Unique job identifier.
            backup_type: Backup strategy to apply.
            interval_seconds: Seconds between each run.

        Returns:
            The created :class:`ScheduledJob`.
        """
        job = ScheduledJob(job_id, backup_type, interval_seconds)
        with self._lock:
            self._jobs.append(job)
        return job

    def remove_job(self, job_id: str) -> None:
        """Removes a job by ID."""
        with self._lock:
            self._jobs = [j for j in self._jobs if j.job_id != job_id]

    def list_jobs(self) -> List[ScheduledJob]:
        """Returns all registered jobs."""
        with self._lock:
            return list(self._jobs)

    def start(self) -> None:
        """Starts the background scheduling thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signals the scheduling thread to stop and waits for it to exit."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run_loop(self) -> None:
        """Internal loop checking each job every second."""
        while not self._stop_event.is_set():
            now = time.monotonic()
            with self._lock:
                jobs_snapshot = list(self._jobs)

            for job in jobs_snapshot:
                if not job.enabled:
                    continue
                if job.last_run is None or (now - job.last_run) >= job.interval_seconds:
                    try:
                        self._callback(job.backup_type)
                        job.last_run = now
                        job.run_count += 1
                    except Exception:
                        pass  # Never crash the scheduler

            self._stop_event.wait(timeout=1.0)
