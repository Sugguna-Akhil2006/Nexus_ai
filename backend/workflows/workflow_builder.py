"""Fluent builder API for composing WorkflowDefinition objects."""

from typing import Any, Dict, List, Optional
from backend.workflows.models import (
    ParallelBranch,
    StepType,
    WorkflowDefinition,
    WorkflowStep,
)


class WorkflowBuilder:
    """Provides a fluent interface for building workflow definitions.

    Example::

        workflow = (
            WorkflowBuilder("Resume Pipeline")
            .add_step("Upload", StepType.RESUME)
            .add_step("Analyze", StepType.REASONING, max_retries=2)
            .build()
        )
    """

    def __init__(self, name: str, description: str = "") -> None:
        self._name = name
        self._description = description
        self._steps: List[WorkflowStep] = []
        self._branches: List[ParallelBranch] = []
        self._variables: Dict[str, Any] = {}
        self._tags: List[str] = []

    def add_step(
        self,
        name: str,
        step_type: StepType,
        parameters: Optional[Dict[str, Any]] = None,
        max_retries: int = 0,
        timeout_seconds: float = 30.0,
        condition: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
    ) -> "WorkflowBuilder":
        """Appends a sequential step to the workflow.

        Args:
            name: Human-readable step label.
            step_type: The intelligence module type for this step.
            parameters: Optional step-specific parameter overrides.
            max_retries: Number of retry attempts on failure.
            timeout_seconds: Per-attempt timeout limit.
            condition: Python expression evaluated before executing the step.
            depends_on: List of step_ids that must complete first.

        Returns:
            ``self`` for method chaining.
        """
        step = WorkflowStep(
            name=name,
            step_type=step_type,
            parameters=parameters or {},
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            condition=condition,
            depends_on=depends_on or [],
        )
        self._steps.append(step)
        return self

    def add_parallel_branch(
        self,
        branch_name: str,
        steps: List[WorkflowStep],
    ) -> "WorkflowBuilder":
        """Adds a parallel branch containing steps that will run concurrently.

        Args:
            branch_name: Label for this parallel group.
            steps: List of ``WorkflowStep`` objects to run concurrently.

        Returns:
            ``self`` for method chaining.
        """
        branch = ParallelBranch(name=branch_name, steps=steps)
        self._branches.append(branch)
        return self

    def set_variable(self, key: str, value: Any) -> "WorkflowBuilder":
        """Sets a workflow-level variable available to all steps.

        Args:
            key: Variable name.
            value: Initial value.

        Returns:
            ``self`` for method chaining.
        """
        self._variables[key] = value
        return self

    def add_tag(self, tag: str) -> "WorkflowBuilder":
        """Adds a metadata tag for discovery and filtering.

        Returns:
            ``self`` for method chaining.
        """
        self._tags.append(tag)
        return self

    def build(self) -> WorkflowDefinition:
        """Constructs and returns the final ``WorkflowDefinition``.

        Returns:
            A complete ``WorkflowDefinition`` ready for registration or execution.
        """
        return WorkflowDefinition(
            name=self._name,
            description=self._description,
            steps=list(self._steps),
            parallel_branches=list(self._branches),
            variables=dict(self._variables),
            tags=list(self._tags),
        )
