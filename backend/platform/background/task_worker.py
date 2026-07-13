"""Task worker module pulling from QueueManager and executing tasks."""

import threading
import time
from typing import Dict, Any, Callable, Optional

from backend.platform.background.queue_manager import QueueManager


class TaskWorkerPool:
    """Worker pool running background loops to execute queued tasks."""

    def __init__(
        self,
        queue_manager: QueueManager,
        executor_fn: Callable[[Dict[str, Any]], None],
        num_workers: int = 2
    ) -> None:
        """Initializes settings.

        Args:
            queue_manager: Tasks source.
            executor_fn: Target callable to run task payload.
            num_workers: Total active worker threads.
        """
        self.queue_manager = queue_manager
        self.executor_fn = executor_fn
        self.num_workers = num_workers
        self._workers: list[threading.Thread] = []
        self._running = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Starts worker threads."""
        with self._lock:
            if self._running:
                return
            self._running = True

        for i in range(self.num_workers):
            t = threading.Thread(target=self._worker_loop, name=f"task-worker-{i}", daemon=True)
            t.start()
            self._workers.append(t)

    def stop(self) -> None:
        """Stops worker loops."""
        with self._lock:
            self._running = False
        for t in self._workers:
            t.join(timeout=1.0)
        self._workers.clear()

    def _worker_loop(self) -> None:
        """Continuously polls and executes tasks from the queue."""
        while True:
            with self._lock:
                if not self._running:
                    break
            
            task = self.queue_manager.dequeue()
            if not task:
                time.sleep(0.2)
                continue

            try:
                self.executor_fn(task)
            except Exception as e:
                # Dispatch to queue manager to decide on DLQ or retry
                self.queue_manager.handle_failure(task, str(e))
