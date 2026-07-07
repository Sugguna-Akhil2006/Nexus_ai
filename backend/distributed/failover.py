"""Failover - detects node failures and reschedules orphaned tasks."""

from __future__ import annotations

import threading
from typing import List, Optional

from backend.distributed.models import DistributedTask, DistributedTaskStatus
from backend.distributed.distributed_queue import DistributedQueue
from backend.distributed.worker_registry import WorkerRegistry
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger


class FailoverManager:
    """Detects worker failures and reschedules any tasks assigned to lost nodes.

    When the :class:`~backend.distributed.heartbeat.HeartbeatMonitor` marks a
    node offline, it calls :meth:`handle_node_failure` which:

    1. Identifies all tasks assigned to the failed node.
    2. Requeues retryable tasks back into the distributed queue.
    3. Marks exhausted tasks as permanently failed.

    Args:
        queue: DistributedQueue holding all tracked tasks.
        registry: WorkerRegistry providing node state.
    """

    def __init__(self, queue: DistributedQueue, registry: WorkerRegistry) -> None:
        self._queue = queue
        self._registry = registry
        self._event_bus = EventBus()
        self._logger = StructuredLogger()
        self._lock = threading.Lock()

    def handle_node_failure(self, node_id: str) -> List[DistributedTask]:
        """Reschedules tasks assigned to a failed node.

        Args:
            node_id: Identifier of the failed worker node.

        Returns:
            List of tasks that were requeued.
        """
        requeued: List[DistributedTask] = []

        with self._lock:
            all_tasks = self._queue.list_all()
            orphaned = [
                t for t in all_tasks
                if t.assigned_node_id == node_id
                and t.status in (DistributedTaskStatus.DISPATCHED, DistributedTaskStatus.RUNNING)
            ]

            for task in orphaned:
                if task.attempts < task.max_retries:
                    self._queue.requeue(task)
                    requeued.append(task)
                    self._logger.warning(
                        f"Task '{task.task_id}' requeued after node '{node_id}' failure "
                        f"(attempt {task.attempts}/{task.max_retries})."
                    )
                else:
                    task.status = DistributedTaskStatus.FAILED
                    task.error = f"Node '{node_id}' failed; max retries exhausted."
                    self._logger.error(
                        f"Task '{task.task_id}' permanently failed after {task.attempts} attempts."
                    )

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="FailoverManager",
            payload={
                "event": "failover.triggered",
                "failed_node_id": node_id,
                "requeued_tasks": len(requeued),
            },
        ))

        return requeued

    def get_failed_tasks(self) -> List[DistributedTask]:
        """Returns all permanently failed tasks.

        Returns:
            List of failed DistributedTask instances.
        """
        return [t for t in self._queue.list_all() if t.status == DistributedTaskStatus.FAILED]
