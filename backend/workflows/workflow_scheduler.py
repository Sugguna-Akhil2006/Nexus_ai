"""Schedules deferred or recurring workflow executions without duplicating Runtime scheduling."""

import threading
import time
from typing import Any, Callable, Dict, Optional

from backend.workflows.models import WorkflowDefinition, WorkflowExecution
from backend.workflows.workflow_context import WorkflowContext
from backend.workflows.workflow_executor import WorkflowExecutor


class WorkflowScheduler:
    """Runs workflows on a delay or at a fixed interval in background threads."""

    def __init__(self, executor: WorkflowExecutor) -> None:
        self._executor = executor
        self._lock = threading.Lock()
        self._scheduled: Dict[str, threading.Timer] = {}

    def schedule_once(
        self,
        workflow_id: str,
        definition: WorkflowDefinition,
        variables: Optional[Dict[str, Any]] = None,
        delay_seconds: float = 0.0,
        callback: Optional[Callable[[WorkflowExecution], None]] = None,
    ) -> str:
        """Schedules a workflow to run once after ``delay_seconds``.

        Args:
            workflow_id: Unique scheduling key (used for cancellation).
            definition: The workflow definition to execute.
            variables: Optional initial context variables.
            delay_seconds: Seconds to wait before execution starts.
            callback: Optional callable invoked with the ``WorkflowExecution`` result.

        Returns:
            The ``workflow_id`` scheduling key.
        """
        def _run():
            ctx = WorkflowContext(workspace_id="scheduler", variables=variables or {})
            result = self._executor.execute(definition, ctx)
            if callback:
                callback(result)
            with self._lock:
                self._scheduled.pop(workflow_id, None)

        timer = threading.Timer(delay_seconds, _run)
        with self._lock:
            self._scheduled[workflow_id] = timer
        timer.daemon = True
        timer.start()
        return workflow_id

    def cancel_scheduled(self, workflow_id: str) -> bool:
        """Cancels a pending scheduled workflow before it starts.

        Args:
            workflow_id: The scheduling key returned by ``schedule_once``.

        Returns:
            ``True`` if found and cancelled, ``False`` otherwise.
        """
        with self._lock:
            timer = self._scheduled.pop(workflow_id, None)
        if timer:
            timer.cancel()
            return True
        return False

    def list_scheduled(self) -> list:
        """Returns the IDs of all currently scheduled (not yet started) workflows."""
        with self._lock:
            return list(self._scheduled.keys())
