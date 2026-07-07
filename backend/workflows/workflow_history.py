"""Thread-safe in-memory persistence layer for workflow execution records."""

import threading
from typing import Dict, List, Optional
from backend.workflows.models import WorkflowExecution


class WorkflowHistory:
    """Stores and retrieves past workflow execution records."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, WorkflowExecution] = {}

    def save(self, execution: WorkflowExecution) -> None:
        """Persists or updates an execution record."""
        with self._lock:
            self._store[execution.execution_id] = execution

    def get(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Returns the execution record for a given execution ID, or None."""
        with self._lock:
            return self._store.get(execution_id)

    def list_by_workflow(self, workflow_id: str) -> List[WorkflowExecution]:
        """Returns all execution records belonging to a specific workflow."""
        with self._lock:
            return [e for e in self._store.values() if e.workflow_id == workflow_id]

    def list_all(self) -> List[WorkflowExecution]:
        """Returns all stored execution records."""
        with self._lock:
            return list(self._store.values())
