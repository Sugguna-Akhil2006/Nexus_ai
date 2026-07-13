"""Job scheduler module managing timed execution triggers (delayed or recurring)."""

import threading
import time
from typing import Dict, Any, Callable, List, Optional


class JobScheduler:
    """Schedules tasks for asynchronous triggering in a thread-safe scheduler registry."""

    def __init__(self) -> None:
        """Initializes internal job tables."""
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def schedule_once(self, job_id: str, trigger_at: float, task_fn: Callable[[], None]) -> None:
        """Schedules a one-off task execution at a future epoch timestamp.

        Args:
            job_id: Unique task identifier.
            trigger_at: Future epoch timestamp.
            task_fn: Callable executing the job logic.
        """
        with self._lock:
            self._jobs[job_id] = {
                "type": "once",
                "trigger_at": trigger_at,
                "task_fn": task_fn,
                "completed": False
            }

    def schedule_recurring(self, job_id: str, interval_seconds: float, task_fn: Callable[[], None]) -> None:
        """Schedules a recurring task execution.

        Args:
            job_id: Unique identifier.
            interval_seconds: Delay interval in seconds.
            task_fn: Callable executing the job.
        """
        with self._lock:
            self._jobs[job_id] = {
                "type": "recurring",
                "interval": interval_seconds,
                "trigger_at": time.time() + interval_seconds,
                "task_fn": task_fn,
                "completed": False
            }

    def cancel_job(self, job_id: str) -> bool:
        """Removes a job from the scheduler list.

        Args:
            job_id: The job ID to cancel.
        """
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                return True
            return False

    def start(self) -> None:
        """Starts the background scheduler poll thread."""
        with self._lock:
            if self._running:
                return
            self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the scheduler poll thread."""
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _scheduler_loop(self) -> None:
        """Periodic checker executing eligible jobs."""
        while True:
            with self._lock:
                if not self._running:
                    break
                now = time.time()
                for job_id, job in list(self._jobs.items()):
                    if job["completed"]:
                        continue
                    if now >= job["trigger_at"]:
                        # Trigger target task in a separate thread to prevent blocking the loop
                        threading.Thread(target=self._run_job_safely, args=(job,), daemon=True).start()
                        if job["type"] == "once":
                            job["completed"] = True
                            del self._jobs[job_id]
                        else:
                            job["trigger_at"] = now + job["interval"]
            time.sleep(0.01)

    def _run_job_safely(self, job: Dict[str, Any]) -> None:
        """Invokes task_fn catching all exceptions."""
        try:
            job["task_fn"]()
        except Exception:
            pass
