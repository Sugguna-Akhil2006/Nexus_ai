"""Background task queue manager supporting FIFO operations and Dead-Letter Queues (DLQ)."""

from collections import deque
import threading
from typing import Dict, Any, Optional, List


class QueueManager:
    """Manages active job processing queues and failed task DLQs."""

    def __init__(self, dlq_threshold: int = 3) -> None:
        """Initializes queues with thread safety.

        Args:
            dlq_threshold: Max attempts before landing in DLQ.
        """
        self.dlq_threshold = dlq_threshold
        self._queue: deque[Dict[str, Any]] = deque()
        self._dlq: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def enqueue(self, task: Dict[str, Any]) -> None:
        """Adds a task to the queue, assigning initial retry counts.

        Args:
            task: Task payload dict.
        """
        with self._lock:
            task_copy = dict(task)
            if "attempts" not in task_copy:
                task_copy["attempts"] = 0
            self._queue.append(task_copy)

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Pulls the oldest task from the queue."""
        with self._lock:
            if not self._queue:
                return None
            return self._queue.popleft()

    def handle_failure(self, task: Dict[str, Any], error_msg: str) -> bool:
        """Increments attempts; routing to DLQ if max attempts reached.

        Args:
            task: The failed task dict.
            error_msg: Diagnostic message.

        Returns:
            True if sent to DLQ, False if re-enqueued.
        """
        with self._lock:
            task["attempts"] = task.get("attempts", 0) + 1
            task["last_error"] = error_msg
            
            if task["attempts"] >= self.dlq_threshold:
                self._dlq.append(task)
                return True
            else:
                self._queue.append(task)
                return False

    def get_dlq_tasks(self) -> List[Dict[str, Any]]:
        """Returns copies of all tasks in the DLQ."""
        with self._lock:
            return list(self._dlq)

    def clear_dlq(self) -> None:
        """Purges the DLQ."""
        with self._lock:
            self._dlq.clear()
            
    def size(self) -> int:
        """Returns current queue size."""
        with self._lock:
            return len(self._queue)
