"""Validates WorkflowDefinition objects before registration or execution."""

from typing import List
from backend.workflows.models import WorkflowDefinition, WorkflowStep


class WorkflowValidationError(ValueError):
    """Raised when a workflow definition fails structural validation."""


class WorkflowValidator:
    """Validates workflow definitions for correctness and completeness."""

    _VALID_TIMEOUT_RANGE = (0.1, 3600.0)
    _MAX_RETRIES = 10

    def validate(self, definition: WorkflowDefinition) -> None:
        """Validates the entire workflow definition.

        Args:
            definition: The ``WorkflowDefinition`` to validate.

        Raises:
            WorkflowValidationError: When any constraint is violated.
        """
        if not definition.name or not definition.name.strip():
            raise WorkflowValidationError("Workflow must have a non-empty name.")

        has_steps = bool(definition.steps) or bool(definition.parallel_branches)
        if not has_steps:
            raise WorkflowValidationError(
                f"Workflow '{definition.name}' must define at least one step or parallel branch."
            )

        all_step_ids: List[str] = [s.step_id for s in definition.steps]
        for branch in definition.parallel_branches:
            all_step_ids.extend(s.step_id for s in branch.steps)

        seen_ids: set = set()
        for step in definition.steps:
            self._validate_step(step, seen_ids, all_step_ids)

        for branch in definition.parallel_branches:
            for step in branch.steps:
                self._validate_step(step, seen_ids, all_step_ids)

    def _validate_step(
        self,
        step: WorkflowStep,
        seen_ids: set,
        all_step_ids: List[str],
    ) -> None:
        """Validates a single step definition."""
        if step.step_id in seen_ids:
            raise WorkflowValidationError(
                f"Duplicate step_id detected: '{step.step_id}'."
            )
        seen_ids.add(step.step_id)

        if not step.name or not step.name.strip():
            raise WorkflowValidationError(
                f"Step '{step.step_id}' must have a non-empty name."
            )

        lo, hi = self._VALID_TIMEOUT_RANGE
        if not (lo <= step.timeout_seconds <= hi):
            raise WorkflowValidationError(
                f"Step '{step.name}' timeout {step.timeout_seconds}s is outside "
                f"the valid range [{lo}, {hi}]."
            )

        if step.max_retries < 0 or step.max_retries > self._MAX_RETRIES:
            raise WorkflowValidationError(
                f"Step '{step.name}' max_retries={step.max_retries} must be "
                f"between 0 and {self._MAX_RETRIES}."
            )

        for dep in step.depends_on:
            if dep not in all_step_ids:
                raise WorkflowValidationError(
                    f"Step '{step.name}' depends on unknown step_id '{dep}'."
                )
