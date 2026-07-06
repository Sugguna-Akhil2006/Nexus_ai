"""Core execution engine driving sequential, parallel, retry, and timeout logic."""

import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.workflows.models import (
    ExecutionStatus,
    ParallelBranch,
    StepResult,
    StepType,
    WorkflowDefinition,
    WorkflowExecution,
    WorkflowStep,
)
from backend.workflows.workflow_context import WorkflowContext
from backend.workflows.workflow_metrics import WorkflowMetrics

# ---------------------------------------------------------------------------
# Step handler registry
# ---------------------------------------------------------------------------
# Maps StepType → callable(step, context) → Dict[str, Any]
# Handlers are kept deliberately thin — all intelligence logic lives in the
# existing modules; the executor merely dispatches.
# ---------------------------------------------------------------------------

StepHandler = Callable[[WorkflowStep, WorkflowContext], Dict[str, Any]]

_DEFAULT_HANDLERS: Dict[StepType, StepHandler] = {
    # Handlers return a minimal output dict.  In production these would call
    # the real intelligence module service methods.
    StepType.RESUME: lambda step, ctx: {"status": "ok", "module": "Resume", **step.parameters},
    StepType.GITHUB: lambda step, ctx: {"status": "ok", "module": "GitHub", **step.parameters},
    StepType.DOCUMENT: lambda step, ctx: {"status": "ok", "module": "Document", **step.parameters},
    StepType.RESEARCH: lambda step, ctx: {"status": "ok", "module": "Research", **step.parameters},
    StepType.REASONING: lambda step, ctx: {"status": "ok", "module": "Reasoning", **step.parameters},
    StepType.KNOWLEDGE_GRAPH: lambda step, ctx: {"status": "ok", "module": "KnowledgeGraph", **step.parameters},
    StepType.CUSTOM_PLUGIN: lambda step, ctx: {"status": "ok", "module": "Plugin", **step.parameters},
    StepType.NO_OP: lambda step, ctx: {"status": "ok", "module": "NoOp"},
}


class WorkflowExecutor:
    """Executes workflow definitions with retry, timeout, parallel and cancellation support."""

    def __init__(
        self,
        metrics: Optional[WorkflowMetrics] = None,
        step_handlers: Optional[Dict[StepType, StepHandler]] = None,
        max_workers: int = 8,
    ) -> None:
        self._metrics = metrics or WorkflowMetrics()
        self._handlers: Dict[StepType, StepHandler] = {
            **_DEFAULT_HANDLERS,
            **(step_handlers or {}),
        }
        self._max_workers = max_workers
        self._event_bus = EventBus()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def execute(
        self,
        definition: WorkflowDefinition,
        context: WorkflowContext,
    ) -> WorkflowExecution:
        """Runs a workflow definition and returns the final execution record.

        Args:
            definition: The workflow to execute.
            context: Shared variable/cancellation store for this run.

        Returns:
            A completed ``WorkflowExecution`` with step results and status.
        """
        execution = WorkflowExecution(
            workflow_id=definition.workflow_id,
            workflow_name=definition.name,
            status=ExecutionStatus.RUNNING,
            variables=context.all_variables(),
        )

        self._publish("workflow.started", {
            "execution_id": execution.execution_id,
            "workflow_id": definition.workflow_id,
            "workflow_name": definition.name,
        })

        wall_start = time.perf_counter()

        try:
            # Sequential steps
            for step in definition.steps:
                if context.is_cancelled:
                    execution.status = ExecutionStatus.CANCELLED
                    break

                result = self._run_step(step, context, execution.execution_id)
                execution.step_results.append(result)

                if result.status == ExecutionStatus.FAILED:
                    execution.status = ExecutionStatus.FAILED
                    execution.errors.append(f"Step '{step.name}' failed: {result.error}")
                    break
                elif result.status == ExecutionStatus.TIMED_OUT:
                    execution.status = ExecutionStatus.TIMED_OUT
                    execution.errors.append(f"Step '{step.name}' timed out.")
                    break
            else:
                # Parallel branches (only if sequential steps all passed)
                if definition.parallel_branches and execution.status == ExecutionStatus.RUNNING:
                    branch_error = self._run_parallel_branches(
                        definition.parallel_branches, context, execution
                    )
                    if branch_error:
                        execution.status = ExecutionStatus.FAILED
                        execution.errors.append(branch_error)

            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED

        except Exception as exc:
            execution.status = ExecutionStatus.FAILED
            execution.errors.append(str(exc))

        finally:
            wall_end = time.perf_counter()
            execution.duration_seconds = round(wall_end - wall_start, 4)
            execution.ended_at = datetime.utcnow().isoformat()
            execution.variables = context.all_variables()

        event_name = (
            "workflow.completed"
            if execution.status == ExecutionStatus.COMPLETED
            else "workflow.failed"
        )
        self._publish(event_name, {
            "execution_id": execution.execution_id,
            "workflow_id": definition.workflow_id,
            "status": execution.status.value,
            "duration_seconds": execution.duration_seconds,
        })

        self._metrics.record_execution_result(
            execution_id=execution.execution_id,
            workflow_id=definition.workflow_id,
            status=execution.status.value,
            duration_seconds=execution.duration_seconds,
            step_count=len(execution.step_results),
        )

        return execution

    # ------------------------------------------------------------------
    # Step execution with retry + timeout
    # ------------------------------------------------------------------

    def _run_step(
        self,
        step: WorkflowStep,
        context: WorkflowContext,
        execution_id: str,
    ) -> StepResult:
        """Executes a single step with retry and timeout enforcement."""
        # Evaluate optional condition guard
        if step.condition and not context.evaluate_condition(step.condition):
            return StepResult(
                step_id=step.step_id,
                step_name=step.name,
                status=ExecutionStatus.SKIPPED,
            )

        handler = self._handlers.get(step.step_type)
        if handler is None:
            return StepResult(
                step_id=step.step_id,
                step_name=step.name,
                status=ExecutionStatus.FAILED,
                error=f"No handler registered for step type '{step.step_type}'.",
            )

        step_start = time.perf_counter()
        last_error = ""
        attempts = 0

        for attempt in range(step.max_retries + 1):
            attempts = attempt + 1
            try:
                with ThreadPoolExecutor(max_workers=1) as pool:
                    future: Future = pool.submit(handler, step, context)
                    output = future.result(timeout=step.timeout_seconds)

                duration = round(time.perf_counter() - step_start, 4)
                context.store_output(step.step_id, output)

                result = StepResult(
                    step_id=step.step_id,
                    step_name=step.name,
                    status=ExecutionStatus.COMPLETED,
                    output=output,
                    attempts=attempts,
                    duration_seconds=duration,
                    ended_at=datetime.utcnow().isoformat(),
                )
                self._publish("workflow.step.completed", {
                    "execution_id": execution_id,
                    "step_id": step.step_id,
                    "step_name": step.name,
                    "status": "COMPLETED",
                    "attempt": attempts,
                })
                self._metrics.record_step_completion(
                    execution_id, step.step_id, step.name, "COMPLETED", duration
                )
                return result

            except FuturesTimeout:
                last_error = f"Timed out after {step.timeout_seconds}s (attempt {attempts})."
                # Don't retry on timeout — treat as terminal
                duration = round(time.perf_counter() - step_start, 4)
                self._metrics.record_step_completion(
                    execution_id, step.step_id, step.name, "TIMED_OUT", duration
                )
                return StepResult(
                    step_id=step.step_id,
                    step_name=step.name,
                    status=ExecutionStatus.TIMED_OUT,
                    error=last_error,
                    attempts=attempts,
                    duration_seconds=duration,
                    ended_at=datetime.utcnow().isoformat(),
                )

            except Exception as exc:
                last_error = str(exc)
                # Retry if attempts remain
                if attempt < step.max_retries:
                    continue

        # All retries exhausted
        duration = round(time.perf_counter() - step_start, 4)
        self._metrics.record_step_completion(
            execution_id, step.step_id, step.name, "FAILED", duration
        )
        return StepResult(
            step_id=step.step_id,
            step_name=step.name,
            status=ExecutionStatus.FAILED,
            error=last_error,
            attempts=attempts,
            duration_seconds=duration,
            ended_at=datetime.utcnow().isoformat(),
        )

    # ------------------------------------------------------------------
    # Parallel branch execution
    # ------------------------------------------------------------------

    def _run_parallel_branches(
        self,
        branches: list,
        context: WorkflowContext,
        execution: WorkflowExecution,
    ) -> str:
        """Runs all branches concurrently, collecting results.

        Returns:
            Empty string on success, or a combined error message on failure.
        """
        errors = []

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            branch_futures: Dict[str, Future] = {}
            for branch in branches:
                branch_futures[branch.branch_id] = pool.submit(
                    self._run_branch, branch, context, execution
                )

            for branch_id, future in branch_futures.items():
                try:
                    branch_errors = future.result(timeout=300.0)
                    errors.extend(branch_errors)
                except Exception as exc:
                    errors.append(f"Branch '{branch_id}' raised: {exc}")

        return "; ".join(errors)

    def _run_branch(
        self,
        branch: ParallelBranch,
        context: WorkflowContext,
        execution: WorkflowExecution,
    ) -> list:
        """Runs all steps within a single parallel branch sequentially."""
        branch_errors = []
        for step in branch.steps:
            if context.is_cancelled:
                break
            result = self._run_step(step, context, execution.execution_id)
            execution.step_results.append(result)
            if result.status in (ExecutionStatus.FAILED, ExecutionStatus.TIMED_OUT):
                branch_errors.append(f"Step '{step.name}': {result.error}")
                break
        return branch_errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _publish(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Publishes a workflow lifecycle event onto the EventBus."""
        try:
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="WorkflowExecutor",
                payload={"event": event_name, **payload},
            ))
        except Exception:
            pass  # Never let event publishing crash the executor
