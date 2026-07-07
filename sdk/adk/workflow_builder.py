"""WorkflowBuilder - composing sequential, parallel, conditional, and loop workflows."""

from __future__ import annotations

import time
import concurrent.futures
from typing import Any, Callable, Dict, List, Optional

from sdk.adk.models import RetryPolicy, WorkflowStep, WorkflowStepType


class WorkflowBuilder:
    """Fluent builder for composing multi-step agent workflows.

    Supports sequential, parallel, conditional, and loop step types
    with per-step timeout and retry controls.

    Example::

        workflow = (
            WorkflowBuilder()
            .sequential("fetch_resume", tool_fn)
            .parallel("analyze_sections", [fn_a, fn_b])
            .conditional("validate", validate_fn, condition=is_valid)
            .loop("retry_extraction", extract_fn, loop_count=3)
            .build()
        )
    """

    def __init__(self) -> None:
        self._steps: List[WorkflowStep] = []
        self._tool_registry: Dict[str, Callable[..., Any]] = {}

    def sequential(
        self,
        name: str,
        fn: Callable[..., Any],
        timeout_seconds: float = 30.0,
        retry_policy: RetryPolicy = RetryPolicy.NONE,
        max_retries: int = 0,
    ) -> "WorkflowBuilder":
        """Adds a sequential step executing the callable in order.

        Args:
            name: Step label.
            fn: Callable to execute.
            timeout_seconds: Max allowed execution time.
            retry_policy: Retry strategy on failure.
            max_retries: Maximum retry attempts.

        Returns:
            Self for method chaining.
        """
        self._tool_registry[name] = fn
        self._steps.append(
            WorkflowStep(
                name=name,
                step_type=WorkflowStepType.SEQUENTIAL,
                tool_name=name,
                timeout_seconds=timeout_seconds,
                retry_policy=retry_policy,
                max_retries=max_retries,
            )
        )
        return self

    def parallel(
        self,
        name: str,
        fns: List[Callable[..., Any]],
        timeout_seconds: float = 60.0,
    ) -> "WorkflowBuilder":
        """Adds a parallel step running multiple callables concurrently.

        Args:
            name: Step label.
            fns: List of callables to run in parallel.
            timeout_seconds: Max allowed total execution time.

        Returns:
            Self for method chaining.
        """
        def _parallel_runner(*args: Any, **kwargs: Any) -> List[Any]:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(f, *args, **kwargs) for f in fns]
                return [f.result(timeout=timeout_seconds) for f in futures]

        self._tool_registry[name] = _parallel_runner
        self._steps.append(
            WorkflowStep(
                name=name,
                step_type=WorkflowStepType.PARALLEL,
                tool_name=name,
                timeout_seconds=timeout_seconds,
            )
        )
        return self

    def conditional(
        self,
        name: str,
        fn: Callable[..., Any],
        condition: Callable[..., bool],
        timeout_seconds: float = 30.0,
    ) -> "WorkflowBuilder":
        """Adds a conditional step executing only when the condition is truthy.

        Args:
            name: Step label.
            fn: Callable to execute if condition passes.
            condition: Callable returning bool guard.
            timeout_seconds: Max allowed execution time.

        Returns:
            Self for method chaining.
        """
        self._tool_registry[name] = fn
        self._steps.append(
            WorkflowStep(
                name=name,
                step_type=WorkflowStepType.CONDITIONAL,
                tool_name=name,
                condition=condition,
                timeout_seconds=timeout_seconds,
            )
        )
        return self

    def loop(
        self,
        name: str,
        fn: Callable[..., Any],
        loop_count: int = 3,
        timeout_seconds: float = 30.0,
        retry_policy: RetryPolicy = RetryPolicy.NONE,
        max_retries: int = 0,
    ) -> "WorkflowBuilder":
        """Adds a loop step executing the callable N times.

        Args:
            name: Step label.
            fn: Callable to iterate.
            loop_count: Number of iterations.
            timeout_seconds: Max allowed execution time per iteration.
            retry_policy: Retry strategy on failure.
            max_retries: Maximum retry attempts per iteration.

        Returns:
            Self for method chaining.
        """
        self._tool_registry[name] = fn
        self._steps.append(
            WorkflowStep(
                name=name,
                step_type=WorkflowStepType.LOOP,
                tool_name=name,
                loop_count=loop_count,
                timeout_seconds=timeout_seconds,
                retry_policy=retry_policy,
                max_retries=max_retries,
            )
        )
        return self

    def build(self) -> List[WorkflowStep]:
        """Returns the ordered list of configured workflow steps.

        Returns:
            List of WorkflowStep instances.
        """
        return list(self._steps)

    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes the workflow steps in defined order, returning per-step results.

        Args:
            context: Optional shared execution context dictionary.

        Returns:
            Dictionary mapping step names to their results.
        """
        ctx = context or {}
        results: Dict[str, Any] = {}

        for step in self._steps:
            fn = self._tool_registry.get(step.tool_name or step.name)
            if fn is None:
                continue

            attempt = 0
            while True:
                try:
                    if step.step_type == WorkflowStepType.CONDITIONAL:
                        if step.condition and not step.condition(ctx):
                            results[step.name] = "skipped"
                            break
                    elif step.step_type == WorkflowStepType.LOOP:
                        loop_results = []
                        for _ in range(step.loop_count):
                            loop_results.append(fn(ctx))
                        results[step.name] = loop_results
                        break
                    else:
                        results[step.name] = fn(ctx)
                        break
                except Exception as exc:
                    attempt += 1
                    if step.retry_policy == RetryPolicy.NONE or attempt > step.max_retries:
                        results[step.name] = {"error": str(exc)}
                        break
                    delay = attempt if step.retry_policy == RetryPolicy.FIXED else 2 ** attempt
                    time.sleep(delay)

        return results
