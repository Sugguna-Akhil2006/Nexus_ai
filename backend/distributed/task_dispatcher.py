"""TaskDispatcher - dispatches tasks to selected worker nodes for execution."""

from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from backend.distributed.models import DistributedTask, DistributedTaskStatus, WorkerNode
from backend.distributed.distributed_queue import DistributedQueue
from backend.distributed.scheduler import Scheduler
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger


class TaskDispatcher:
    """Dequeues tasks and dispatches them to scheduled worker nodes.

    This dispatcher runs a background thread that continuously polls the
    queue, selects a worker via the scheduler, and invokes the configured
    execution handler.

    Args:
        queue: DistributedQueue to consume tasks from.
        scheduler: Scheduler for node selection.
        execute_fn: Callable invoked with (task, node) to perform execution.
        poll_interval_seconds: Polling frequency.
    """

    def __init__(
        self,
        queue: DistributedQueue,
        scheduler: Scheduler,
        execute_fn: Optional[Callable[[DistributedTask, WorkerNode], None]] = None,
        poll_interval_seconds: float = 0.5,
    ) -> None:
        self._queue = queue
        self._scheduler = scheduler
        self._execute_fn = execute_fn or self._default_execute
        self._poll_interval = poll_interval_seconds
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._event_bus = EventBus()
        self._logger = StructuredLogger()
        self._active_tasks: Dict[str, DistributedTask] = {}
        self._lock = threading.Lock()

    def start(self) -> None:
        """Starts the background dispatch loop."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._dispatch_loop, daemon=True, name="TaskDispatcher")
        self._thread.start()
        self._logger.info("TaskDispatcher started.")

    def stop(self) -> None:
        """Stops the background dispatch loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 2)
        self._logger.info("TaskDispatcher stopped.")

    def dispatch_now(self, task: DistributedTask) -> Optional[WorkerNode]:
        """Immediately dispatches a single task without waiting for the poll loop.

        Args:
            task: Task to dispatch.

        Returns:
            Assigned WorkerNode or None if no node is available.
        """
        node = self._scheduler.assign(task)
        if not node:
            self._logger.warning(f"No available node for task '{task.task_id}'.")
            return None
        self._fire_task(task, node)
        return node

    def _dispatch_loop(self) -> None:
        """Background loop dequeuing and dispatching tasks."""
        while self._running:
            task = self._queue.dequeue()
            if task:
                node = self._scheduler.assign(task)
                if node:
                    self._fire_task(task, node)
                else:
                    # Re-enqueue if no node available
                    task.status = DistributedTaskStatus.QUEUED
                    self._queue.enqueue(task)
            time.sleep(self._poll_interval)

    def _fire_task(self, task: DistributedTask, node: WorkerNode) -> None:
        """Marks task as running and invokes the execution handler.

        Args:
            task: Task to execute.
            node: Assigned worker node.
        """
        task.status = DistributedTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.assigned_node_id = node.node_id

        with self._lock:
            self._active_tasks[task.task_id] = task

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="TaskDispatcher",
            payload={"event": "task.dispatched", "task_id": task.task_id, "node_id": node.node_id},
        ))

        try:
            self._execute_fn(task, node)
            task.status = DistributedTaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="TaskDispatcher",
                payload={"event": "task.completed", "task_id": task.task_id},
            ))
        except Exception as exc:
            task.status = DistributedTaskStatus.FAILED
            task.error = str(exc)
            self._logger.error(f"Task '{task.task_id}' failed: {exc}")
        finally:
            with self._lock:
                self._active_tasks.pop(task.task_id, None)

    @staticmethod
    def _default_execute(task: DistributedTask, node: WorkerNode) -> None:
        """Default no-op execution handler used in tests."""
        time.sleep(0.01)

    def list_active_tasks(self) -> List[DistributedTask]:
        """Returns tasks currently being executed."""
        with self._lock:
            return list(self._active_tasks.values())
