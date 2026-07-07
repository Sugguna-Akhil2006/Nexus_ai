"""DistributedQueue - thread-safe priority task queue for cluster execution."""

from __future__ import annotations

import heapq
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from backend.distributed.models import DistributedTask, DistributedTaskStatus
from backend.runtime.logger import StructuredLogger


class DistributedQueue:
    """Thread-safe priority queue managing distributed task scheduling.

    Tasks with higher priority values are dequeued first. Equal priorities
    are resolved by insertion order (FIFO).
    """

    def __init__(self) -> None:
        # Heap stores (-priority, sequence, task_id) for max-heap behaviour
        self._heap: List[Tuple[int, int, str]] = []
        self._tasks: Dict[str, DistributedTask] = {}
        self._lock = threading.RLock()
        self._sequence: int = 0
        self._logger = StructuredLogger()

    def enqueue(self, task: DistributedTask) -> None:
        """Adds a task to the priority queue.

        Args:
            task: DistributedTask instance to enqueue.
        """
        with self._lock:
            task.status = DistributedTaskStatus.QUEUED
            self._tasks[task.task_id] = task
            seq = self._sequence
            self._sequence += 1
            heapq.heappush(self._heap, (-task.priority, seq, task.task_id))
            self._logger.info(f"Task '{task.task_id}' enqueued with priority {task.priority}.")

    def dequeue(self) -> Optional[DistributedTask]:
        """Removes and returns the highest-priority queued task.

        Returns:
            DistributedTask or None if the queue is empty.
        """
        with self._lock:
            while self._heap:
                _, _, task_id = heapq.heappop(self._heap)
                task = self._tasks.get(task_id)
                if task and task.status == DistributedTaskStatus.QUEUED:
                    task.status = DistributedTaskStatus.DISPATCHED
                    return task
            return None

    def cancel(self, task_id: str) -> bool:
        """Cancels a queued task.

        Args:
            task_id: Identifier of the task to cancel.

        Returns:
            True if cancelled, False if not found or not cancellable.
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task and task.status == DistributedTaskStatus.QUEUED:
                task.status = DistributedTaskStatus.CANCELLED
                self._logger.info(f"Task '{task_id}' cancelled.")
                return True
            return False

    def requeue(self, task: DistributedTask) -> None:
        """Re-enqueues a failed task for retry.

        Args:
            task: DistributedTask to retry.
        """
        with self._lock:
            task.status = DistributedTaskStatus.RETRYING
            task.attempts += 1
            task.assigned_node_id = None
            self._tasks[task.task_id] = task
            seq = self._sequence
            self._sequence += 1
            heapq.heappush(self._heap, (-task.priority, seq, task.task_id))

    def get_task(self, task_id: str) -> Optional[DistributedTask]:
        """Returns a task by ID without removing it.

        Args:
            task_id: Task identifier.

        Returns:
            DistributedTask or None.
        """
        with self._lock:
            return self._tasks.get(task_id)

    def list_queued(self) -> List[DistributedTask]:
        """Lists all currently queued (not yet dispatched) tasks."""
        with self._lock:
            return [t for t in self._tasks.values() if t.status == DistributedTaskStatus.QUEUED]

    def list_all(self) -> List[DistributedTask]:
        """Lists all tracked tasks regardless of status."""
        with self._lock:
            return list(self._tasks.values())

    def depth(self) -> int:
        """Returns the number of tasks currently queued (not dispatched)."""
        with self._lock:
            return sum(1 for t in self._tasks.values() if t.status == DistributedTaskStatus.QUEUED)

    def clear(self) -> None:
        """Clears all tasks (primarily for tests)."""
        with self._lock:
            self._heap.clear()
            self._tasks.clear()
