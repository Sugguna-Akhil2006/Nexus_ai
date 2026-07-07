"""Top-level AI Workflow Automation Engine facade exposing the full public API."""

import threading
from typing import Any, Dict, List, Optional

from backend.workflows.models import (
    ExecutionStatus,
    WorkflowDefinition,
    WorkflowExecution,
)
from backend.workflows.workflow_builder import WorkflowBuilder
from backend.workflows.workflow_context import WorkflowContext
from backend.workflows.workflow_executor import WorkflowExecutor, StepHandler, StepType
from backend.workflows.workflow_history import WorkflowHistory
from backend.workflows.workflow_metrics import WorkflowMetrics
from backend.workflows.workflow_registry import WorkflowRegistry
from backend.workflows.workflow_scheduler import WorkflowScheduler
from backend.workflows.workflow_templates import get_template, list_templates
from backend.workflows.workflow_validator import WorkflowValidator


class WorkflowEngine:
    """Unified entry point for creating, executing, cancelling, and monitoring workflows.

    All coordination between builder, validator, registry, executor, history,
    metrics and scheduler is handled here — callers never touch the subsystems
    directly.
    """

    def __init__(
        self,
        step_handlers: Optional[Dict[StepType, StepHandler]] = None,
    ) -> None:
        self._registry = WorkflowRegistry()
        self._history = WorkflowHistory()
        self._metrics = WorkflowMetrics()
        self._validator = WorkflowValidator()
        self._executor = WorkflowExecutor(
            metrics=self._metrics,
            step_handlers=step_handlers,
        )
        self._scheduler = WorkflowScheduler(self._executor)

        # Active execution contexts keyed by execution_id for cancellation
        self._active_contexts: Dict[str, WorkflowContext] = {}
        self._ctx_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Workflow lifecycle
    # ------------------------------------------------------------------

    def create_workflow(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        """Validates and registers a workflow definition.

        Args:
            definition: The workflow to validate and store.

        Returns:
            The registered ``WorkflowDefinition`` (unchanged).

        Raises:
            WorkflowValidationError: If the definition fails validation.
        """
        self._validator.validate(definition)
        self._registry.register(definition)
        return definition

    def execute_workflow(
        self,
        workflow_id: str,
        variables: Optional[Dict[str, Any]] = None,
        workspace_id: str = "default",
    ) -> WorkflowExecution:
        """Executes a registered workflow and persists the result in history.

        Args:
            workflow_id: ID of a previously registered workflow.
            variables: Optional runtime variables to inject into the context.
            workspace_id: Workspace identifier propagated through the context.

        Returns:
            The completed ``WorkflowExecution`` record.

        Raises:
            KeyError: If ``workflow_id`` is not registered.
        """
        definition = self._registry.get(workflow_id)
        if definition is None:
            raise KeyError(f"Workflow '{workflow_id}' is not registered.")

        # Merge definition-level defaults with caller-supplied variables
        merged_vars = {**definition.variables, **(variables or {})}
        context = WorkflowContext(workspace_id=workspace_id, variables=merged_vars)

        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_name=definition.name,
        )

        with self._ctx_lock:
            self._active_contexts[execution.execution_id] = context

        try:
            execution = self._executor.execute(definition, context)
        finally:
            with self._ctx_lock:
                self._active_contexts.pop(execution.execution_id, None)
            self._history.save(execution)

        return execution

    def cancel_workflow(self, execution_id: str) -> bool:
        """Signals a running execution to stop after its current step.

        Args:
            execution_id: The execution ID to cancel.

        Returns:
            ``True`` if the execution was found and signalled, ``False`` otherwise.
        """
        with self._ctx_lock:
            ctx = self._active_contexts.get(execution_id)
        if ctx:
            ctx.cancel()
            return True
        return False

    # ------------------------------------------------------------------
    # Status and history
    # ------------------------------------------------------------------

    def get_status(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Returns the execution record for a given execution ID.

        Args:
            execution_id: The execution ID to look up.

        Returns:
            The ``WorkflowExecution`` or ``None`` if not found.
        """
        # Check active context first (execution may still be running)
        execution = self._history.get(execution_id)
        return execution

    def get_history(self, workflow_id: str) -> List[WorkflowExecution]:
        """Returns all past execution records for a specific workflow.

        Args:
            workflow_id: The workflow whose history to retrieve.

        Returns:
            List of ``WorkflowExecution`` objects, most recent last.
        """
        return self._history.list_by_workflow(workflow_id)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Returns aggregated performance metrics across all executions.

        Returns:
            Summary dictionary with counts, averages and success rates.
        """
        return self._metrics.get_summary()

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------

    def list_templates(self) -> List[str]:
        """Returns the names of all available pre-built workflow templates.

        Returns:
            List of template name strings.
        """
        return list_templates()

    def execute_template(
        self,
        template_name: str,
        variables: Optional[Dict[str, Any]] = None,
        workspace_id: str = "default",
    ) -> WorkflowExecution:
        """Builds and immediately executes a named workflow template.

        Args:
            template_name: The registered template identifier.
            variables: Optional runtime variables.
            workspace_id: Workspace context identifier.

        Returns:
            The completed ``WorkflowExecution`` record.

        Raises:
            KeyError: If the template name is not recognised.
        """
        definition = get_template(template_name)
        self._validator.validate(definition)
        # Register transiently so execute_workflow can look it up
        self._registry.register(definition)
        return self.execute_workflow(
            definition.workflow_id,
            variables=variables,
            workspace_id=workspace_id,
        )

    # ------------------------------------------------------------------
    # Registry introspection
    # ------------------------------------------------------------------

    def list_workflows(self) -> List[WorkflowDefinition]:
        """Returns all registered workflow definitions."""
        return self._registry.list_all()

    def delete_workflow(self, workflow_id: str) -> bool:
        """Removes a workflow definition from the registry.

        Args:
            workflow_id: The workflow ID to remove.

        Returns:
            ``True`` if found and removed, ``False`` otherwise.
        """
        return self._registry.delete(workflow_id)
