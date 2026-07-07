"""ExecutionCoordinator - maintains workflow and task state across the cluster."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.distributed.models import DistributedTask, DistributedTaskStatus
from backend.distributed.distributed_queue import DistributedQueue
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger


class WorkflowState:
    """In-memory state tracker for a distributed workflow.

    Attributes:
        workflow_id: Unique workflow identifier.
        status: Overall workflow status string.
        tasks: Ordered list of associated task IDs.
        metadata: Arbitrary workflow metadata.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
    """

    def __init__(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        self.workflow_id = workflow_id
        self.status: str = "pending"
        self.tasks: List[str] = []
        self.metadata: Dict[str, Any] = metadata or {}
        self.created_at: datetime = datetime.utcnow()
        self.updated_at: datetime = datetime.utcnow()

    def add_task(self, task_id: str) -> None:
        """Adds a task ID to the workflow's task list."""
        self.tasks.append(task_id)
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Serialises the workflow state."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status,
            "tasks": list(self.tasks),
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ExecutionCoordinator:
    """Maintains the state of distributed workflows and their constituent tasks.

    Provides a single source of truth for:
    - Workflow registration and status tracking.
    - Task state transitions.
    - Execution progress reporting.

    Args:
        queue: DistributedQueue used to look up task state.
    """

    def __init__(self, queue: DistributedQueue) -> None:
        self._queue = queue
        self._workflows: Dict[str, WorkflowState] = {}
        self._lock = threading.RLock()
        self._event_bus = EventBus()
        self._logger = StructuredLogger()

    def register_workflow(self, workflow_id: str, metadata: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """Creates and registers a new workflow state container.

        Args:
            workflow_id: Unique workflow identifier.
            metadata: Optional metadata dictionary.

        Returns:
            Newly created WorkflowState.
        """
        with self._lock:
            state = WorkflowState(workflow_id, metadata)
            self._workflows[workflow_id] = state
            self._logger.info(f"Workflow '{workflow_id}' registered.")
        return state

    def add_task_to_workflow(self, workflow_id: str, task: DistributedTask) -> None:
        """Associates a task with a workflow.

        Args:
            workflow_id: Workflow to associate with.
            task: DistributedTask to track.
        """
        with self._lock:
            state = self._workflows.get(workflow_id)
            if state:
                state.add_task(task.task_id)

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Returns current progress metrics for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Progress dictionary with counts and completion percentage.
        """
        with self._lock:
            state = self._workflows.get(workflow_id)
            if not state:
                return {"error": f"Workflow '{workflow_id}' not found."}

            task_ids = list(state.tasks)

        statuses: Dict[str, int] = {s.value: 0 for s in DistributedTaskStatus}
        for tid in task_ids:
            task = self._queue.get_task(tid)
            if task:
                statuses[task.status.value] = statuses.get(task.status.value, 0) + 1

        total = len(task_ids)
        completed = statuses.get(DistributedTaskStatus.COMPLETED.value, 0)
        progress_pct = round((completed / total * 100) if total > 0 else 0.0, 1)

        return {
            "workflow_id": workflow_id,
            "total_tasks": total,
            "progress_percent": progress_pct,
            "task_statuses": statuses,
            "workflow_status": state.status,
        }

    def update_workflow_status(self, workflow_id: str, status: str) -> None:
        """Updates the top-level status of a workflow.

        Args:
            workflow_id: Workflow identifier.
            status: New status string.
        """
        with self._lock:
            state = self._workflows.get(workflow_id)
            if state:
                state.status = status
                state.updated_at = datetime.utcnow()

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ExecutionCoordinator",
            payload={"event": "workflow.status_updated", "workflow_id": workflow_id, "status": status},
        ))

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Lists all registered workflow states.

        Returns:
            List of serialised WorkflowState dictionaries.
        """
        with self._lock:
            return [s.to_dict() for s in self._workflows.values()]

    def clear(self) -> None:
        """Clears all workflow state (primarily for tests)."""
        with self._lock:
            self._workflows.clear()
