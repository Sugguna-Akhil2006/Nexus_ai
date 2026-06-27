from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from core.event import Event, EventBus, EventType
from core.exceptions import TaskException, TaskValidationError
from core.logger import StructuredLogger
from core.task import Task
from core.task_queue import QueuePriority


class ExecutionMode(Enum):
    """Execution modes determining the concurrency strategy for runtime dispatching."""
    IMMEDIATE = "IMMEDIATE"
    ASYNC = "ASYNC"
    PARALLEL = "PARALLEL"
    SCHEDULED = "SCHEDULED"
    DISTRIBUTED = "DISTRIBUTED"


@dataclass(frozen=True)
class RetryPolicy:
    """Immutable retry configuration defining task execution backoff logic.

    Attributes:
        max_retries: Maximum number of times to retry a failed task.
        retry_delay: Delay duration in seconds before the first retry.
        exponential_backoff: If True, delay is multiplied by multiplier after each failure.
        backoff_multiplier: The factor by which backoff delay increases.
        retryable_exceptions: List of exception class names that trigger a retry.
    """
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    backoff_multiplier: float = 2.0
    retryable_exceptions: List[str] = field(default_factory=lambda: ["Exception"])

    def validate(self) -> None:
        """Validates retry policy invariants.

        Raises:
            TaskValidationError: If retry parameters are negative or invalid.
        """
        if self.max_retries < 0:
            raise TaskValidationError("max_retries cannot be negative.")
        if self.retry_delay < 0:
            raise TaskValidationError("retry_delay cannot be negative.")
        if self.backoff_multiplier <= 0:
            raise TaskValidationError("backoff_multiplier must be a positive number.")


@dataclass(frozen=True)
class ExecutionPlan:
    """Immutable directive specifying execution constraints, cost, and routing details.

    Attributes:
        plan_id: Unique UUID associated with the plan.
        task: The corresponding Task being planned.
        created_at: Generation timestamp.
        execution_mode: Target execution scheduling category.
        priority: The priority configuration for execution routing.
        retry_policy: Reusable retry config rules.
        timeout: Expiry threshold limit in seconds.
        dependencies: Task UUID dependencies list.
        metadata: Copy of task metadata and options.
        estimated_cost: Calculated processing cost estimate.
        estimated_duration: Estimated execution duration in seconds.
    """
    plan_id: uuid.UUID
    task: Task
    created_at: datetime
    execution_mode: ExecutionMode
    priority: QueuePriority
    retry_policy: RetryPolicy
    timeout: float
    dependencies: List[uuid.UUID]
    metadata: Dict[str, Any]
    estimated_cost: float
    estimated_duration: float


class Planner:
    """Orchestrates deterministic scheduling analysis, validation, and planning for Tasks.

    Planner transforms Task configurations into immutable ExecutionPlans without running them.
    """

    def __init__(self) -> None:
        self.logger = StructuredLogger()
        self.event_bus = EventBus()

    def validate_task(self, task: Task) -> None:
        """Validates that a Task contains the mandatory planning fields.

        Args:
            task: The Task instance to evaluate.

        Raises:
            TaskValidationError: If task features are invalid.
        """
        if not task:
            self.logger.warning("Task validation failed: Task is None.")
            raise TaskValidationError("Task cannot be None.")

        if not getattr(task, "task_id", None):
            self.logger.warning("Task validation failed: Missing task_id UUID attribute.")
            raise TaskValidationError("Task must have a valid task_id.")

        if (
            not getattr(task, "description", None) or
            not str(task.description).strip()
        ):
            self.logger.warning(
                "Task validation failed: Description is empty.",
                task_id=task.task_id
            )
            raise TaskValidationError("Task must have a non-empty description.")

    def estimate_cost(self, task: Task) -> float:
        """Determines estimated cost weight metrics based on description complexity.

        Args:
            task: The Task container.

        Returns:
            float: Processing cost estimate.
        """
        desc = getattr(task, "description", "")
        return round(float(len(desc)) * 0.05, 2)

    def estimate_duration(self, task: Task) -> float:
        """Determines estimated duration threshold values in seconds.

        Args:
            task: The Task container.

        Returns:
            float: Processing duration estimate in seconds.
        """
        desc = getattr(task, "description", "")
        return round(1.0 + float(len(desc)) * 0.02, 2)

    def create_plan(self, task: Task) -> ExecutionPlan:
        """Creates an ExecutionPlan configuration from the given Task.

        Args:
            task: The Task to parse.

        Returns:
            ExecutionPlan: Newly constructed immutable plan.

        Raises:
            TaskValidationError: On invalid configurations.
            TaskException: On runtime planning errors.
        """
        task_id = getattr(task, "task_id", None)
        self.logger.info("Planning started", task_id=task_id)

        try:
            self.validate_task(task)

            # Execution Mode
            mode_str = task.metadata.get("execution_mode", "IMMEDIATE")
            try:
                execution_mode = ExecutionMode[mode_str]
            except KeyError:
                raise TaskValidationError(f"Unsupported execution mode: {mode_str}")

            # Retry Policy
            retry_data = task.metadata.get("retry_policy")
            if retry_data:
                try:
                    retry_policy = RetryPolicy(
                        max_retries=int(retry_data.get("max_retries", 3)),
                        retry_delay=float(retry_data.get("retry_delay", 1.0)),
                        exponential_backoff=bool(retry_data.get("exponential_backoff", True)),
                        backoff_multiplier=float(retry_data.get("backoff_multiplier", 2.0)),
                        retryable_exceptions=list(retry_data.get("retryable_exceptions", ["Exception"]))
                    )
                    retry_policy.validate()
                except Exception as e:
                    if isinstance(e, TaskValidationError):
                        raise
                    raise TaskValidationError(f"Invalid retry policy parameters: {e}") from e
            else:
                retry_policy = RetryPolicy()

            # Priority
            priority_str = task.metadata.get("priority", "NORMAL")
            try:
                priority = QueuePriority[priority_str]
            except KeyError:
                priority = QueuePriority.NORMAL

            # Dependencies
            deps_list = task.metadata.get("dependencies", [])
            dependencies = []
            for dep in deps_list:
                try:
                    dependencies.append(uuid.UUID(str(dep)))
                except ValueError:
                    raise TaskValidationError(f"Invalid dependency UUID: {dep}")

            # Timeout
            timeout = float(task.metadata.get("timeout", 30.0))
            if timeout <= 0:
                raise TaskValidationError("Timeout must be a positive number.")

            plan_id = uuid.uuid4()
            created_at = datetime.utcnow()

            estimated_cost = self.estimate_cost(task)
            estimated_duration = self.estimate_duration(task)

            plan = ExecutionPlan(
                plan_id=plan_id,
                task=task,
                created_at=created_at,
                execution_mode=execution_mode,
                priority=priority,
                retry_policy=retry_policy,
                timeout=timeout,
                dependencies=dependencies,
                metadata=task.metadata.copy(),
                estimated_cost=estimated_cost,
                estimated_duration=estimated_duration
            )

            # Publish event
            event = Event(
                event_type=EventType.CUSTOM_EVENT,
                source="Planner",
                payload={
                    "event_name": "planner.plan.created",
                    "plan_id": str(plan_id),
                    "task_id": str(task_id)
                }
            )
            self.event_bus.publish(event)

            self.logger.info(
                f"Planning completed successfully. Plan ID: {plan_id}",
                task_id=task_id
            )
            return plan

        except Exception as e:
            self.logger.error(
                f"Planning error occurred: {e}",
                task_id=task_id
            )
            event = Event(
                event_type=EventType.ERROR_OCCURRED,
                source="Planner",
                payload={
                    "event_name": "planner.plan.failed",
                    "task_id": str(task_id) if task_id else "",
                    "error": str(e)
                }
            )
            self.event_bus.publish(event)

            if isinstance(e, TaskValidationError):
                raise
            raise TaskException(f"Failed to generate execution plan: {e}") from e
