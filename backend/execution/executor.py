from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger
from backend.execution.planner import ExecutionPlan
from backend.runtime.result import Result, ResultStatus


class ExecutionError(NexusException):
    """Base exception for all executor-related errors."""
    pass


class ExecutionTimeoutError(ExecutionError):
    """Raised when plan execution times out."""
    pass


class CancellationError(ExecutionError):
    """Raised when plan execution is cancelled."""
    pass


class ExecutionNotFoundError(ExecutionError):
    """Raised when the specified execution identifier is not found."""
    pass


class ExecutionStatus(Enum):
    """Lifecycle statuses for executions inside the Executor."""
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    RETRYING = "RETRYING"


@dataclass(frozen=True)
class ExecutionMetrics:
    """Immutable metrics summary of a task execution process.

    Attributes:
        duration: Processing execution duration in seconds.
        cpu_time: Placeholder cpu time in seconds.
        memory_usage: Placeholder memory usage in MB.
        retries: Tracked count of retry attempts.
        timestamps: Dictionary capturing execution timestamps.
        execution_cost: Processing execution cost weight placeholder.
    """
    duration: float = 0.0
    cpu_time: float = 0.0
    memory_usage: float = 0.0
    retries: int = 0
    timestamps: Dict[str, datetime] = field(default_factory=dict)
    execution_cost: float = 0.0


@dataclass
class ExecutionContext:
    """State context tracking a single task execution run.

    Attributes:
        execution_id: Unique UUID identifier.
        execution_plan: The ExecutionPlan being run.
        started_at: Timestamp when execution started.
        completed_at: Optional timestamp when execution completed.
        worker_id: Optional string identifying the active worker.
        attempt: The active attempt count.
        timeout: Expiry timeout threshold in seconds.
        metadata: Copy of execution plan metadata map.
    """
    execution_id: uuid.UUID
    execution_plan: ExecutionPlan
    started_at: datetime
    completed_at: Optional[datetime] = None
    worker_id: Optional[str] = None
    attempt: int = 1
    timeout: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Executor:
    """Thread-safe Singleton executor engine coordinating ExecutionPlan execution."""
    _instance: Optional["Executor"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "Executor":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self.logger = StructuredLogger()
            self.event_bus = EventBus()
            self._contexts: Dict[uuid.UUID, ExecutionContext] = {}
            self._statuses: Dict[uuid.UUID, ExecutionStatus] = {}
            self._metrics: Dict[uuid.UUID, ExecutionMetrics] = {}
            self._cancellations: Set[uuid.UUID] = set()
            self._handlers: Dict[str, Callable[[Any], Any]] = {}
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def register_handler(self, task_description_prefix: str, handler: Callable[[Any], Any]) -> None:
        """Registers a custom callable execution target by task description prefix.

        Args:
            task_description_prefix: Match string prefix.
            handler: Callable task handler.
        """
        with self._lock:
            self._handlers[task_description_prefix] = handler

    def get_handler(self, task_description: str) -> Optional[Callable[[Any], Any]]:
        """Resolves task handler matching description prefix.

        Args:
            task_description: The description of the task.

        Returns:
            Optional[Callable]: Matched handler, or None.
        """
        with self._lock:
            for prefix, handler in self._handlers.items():
                if task_description.startswith(prefix):
                    return handler
            return None

    def status(self, execution_id: Union[uuid.UUID, str]) -> ExecutionStatus:
        """Gets the status of an execution.

        Args:
            execution_id: Unique execution UUID.

        Returns:
            ExecutionStatus: Status enum.

        Raises:
            ExecutionNotFoundError: If execution ID does not exist.
        """
        exec_id = uuid.UUID(str(execution_id)) if not isinstance(execution_id, uuid.UUID) else execution_id
        with self._lock:
            if exec_id not in self._statuses:
                raise ExecutionNotFoundError(f"Execution ID '{exec_id}' not found.")
            return self._statuses[exec_id]

    def metrics(self, execution_id: Union[uuid.UUID, str]) -> Optional[ExecutionMetrics]:
        """Gets execution metrics payload if execution completed.

        Args:
            execution_id: Unique execution UUID.

        Returns:
            Optional[ExecutionMetrics]: The metrics summary, or None.
        """
        exec_id = uuid.UUID(str(execution_id)) if not isinstance(execution_id, uuid.UUID) else execution_id
        with self._lock:
            return self._metrics.get(exec_id)

    def cancel(self, execution_id: Union[uuid.UUID, str]) -> bool:
        """Signals a cancellation request to a running execution.

        Args:
            execution_id: Unique execution UUID.

        Returns:
            bool: True if cancellation request succeeded, False otherwise.
        """
        exec_id = uuid.UUID(str(execution_id)) if not isinstance(execution_id, uuid.UUID) else execution_id
        with self._lock:
            context = self._contexts.get(exec_id)
            if not context:
                self.logger.warning(f"Cancellation failed. Execution ID '{exec_id}' not found.")
                return False

            current_status = self._statuses.get(exec_id)
            if current_status in (
                ExecutionStatus.SUCCESS,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
                ExecutionStatus.TIMEOUT
            ):
                return False

            self._statuses[exec_id] = ExecutionStatus.CANCELLED
            self._cancellations.add(exec_id)
            self._publish_event("executor.cancelled", exec_id, context.execution_plan.plan_id)
            self.logger.info(f"Cancellation request registered. ID: {exec_id}")
            return True

    def is_cancelled(self, execution_id: uuid.UUID) -> bool:
        """Checks if the execution ID has been flagged for cancellation."""
        with self._lock:
            return execution_id in self._cancellations

    def execute(self, plan: ExecutionPlan) -> Result:
        """Executes an ExecutionPlan, applying retry policies, timeouts, and tracking.

        Args:
            plan: The ExecutionPlan to execute.

        Returns:
            Result: Standardized Result outcome.
        """
        execution_id = uuid.uuid4()
        started_at = datetime.utcnow()
        task_id = getattr(plan.task, "task_id", None)

        self.logger.info(f"Execution started. ID: {execution_id}. Plan ID: {plan.plan_id}", task_id=task_id)

        context = ExecutionContext(
            execution_id=execution_id,
            execution_plan=plan,
            started_at=started_at,
            timeout=plan.timeout,
            metadata=plan.metadata.copy()
        )

        with self._lock:
            self._contexts[execution_id] = context
            self._statuses[execution_id] = ExecutionStatus.CREATED

        self._publish_event("executor.started", execution_id, plan.plan_id)

        attempt = 1
        max_retries = plan.retry_policy.max_retries
        retry_delay = plan.retry_policy.retry_delay
        backoff_multiplier = plan.retry_policy.backoff_multiplier
        exponential_backoff = plan.retry_policy.exponential_backoff

        last_exception: Optional[Exception] = None

        while True:
            # Check cancellation before starting attempt
            if self.is_cancelled(execution_id):
                return self._finalize_cancelled(execution_id, context, started_at)

            with self._lock:
                self._statuses[execution_id] = ExecutionStatus.RUNNING
                context.attempt = attempt

            try:
                # Retrieve executable logic
                handler = self.get_handler(plan.task.description)
                
                # Check for agent fallback
                agent_name = plan.metadata.get("agent_name")
                if not handler and agent_name:
                    from backend.runtime.registry import AgentRegistry
                    registry = AgentRegistry()
                    agent = registry.get_agent(agent_name)
                    handler = lambda task: agent.execute_task(task)

                if not handler:
                    # Generic default mock run
                    handler = lambda task: f"Default Executed: {task.description}"

                # Run execution with timeout checks
                output = self._run_with_timeout(lambda: handler(plan.task), plan.timeout)

                # Verification check if cancelled during run
                if self.is_cancelled(execution_id):
                    return self._finalize_cancelled(execution_id, context, started_at)

                return self._finalize_success(execution_id, context, started_at, output, attempt - 1)

            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Attempt {attempt} failed for Execution ID {execution_id}: {e}",
                    task_id=task_id
                )

                if isinstance(e, ExecutionTimeoutError):
                    self._publish_event("executor.timeout", execution_id, plan.plan_id)
                    # Timeouts are considered non-retryable in this default model implementation
                    return self._finalize_timeout(execution_id, context, started_at, e, attempt - 1)

                if self.is_cancelled(execution_id) or isinstance(e, CancellationError):
                    return self._finalize_cancelled(execution_id, context, started_at)

                # Check if retryable exception matches policy exception lists
                exc_class_name = type(e).__name__
                policy_exceptions = plan.retry_policy.retryable_exceptions
                is_retryable = (
                    "Exception" in policy_exceptions or
                    exc_class_name in policy_exceptions
                )

                if is_retryable and attempt <= max_retries:
                    # Delay calculation
                    delay = retry_delay
                    if exponential_backoff:
                        delay = retry_delay * (backoff_multiplier ** (attempt - 1))

                    with self._lock:
                        self._statuses[execution_id] = ExecutionStatus.RETRYING

                    self._publish_event(
                        "executor.retry",
                        execution_id,
                        plan.plan_id,
                        attempt=attempt,
                        next_delay=delay
                    )
                    self.logger.info(
                        f"Scheduling retry attempt {attempt + 1}. Delay: {delay}s.",
                        task_id=task_id
                    )

                    try:
                        self._sleep_with_cancellation_check(execution_id, delay)
                    except CancellationError:
                        return self._finalize_cancelled(execution_id, context, started_at)

                    attempt += 1
                else:
                    break

        # Max retries exhausted or non-retryable exception hit
        return self._finalize_failure(execution_id, context, started_at, last_exception, attempt - 1)

    def _run_with_timeout(self, func: Callable[[], Any], timeout_seconds: float) -> Any:
        result_container: Dict[str, Any] = {}
        exception_container: Dict[str, Exception] = {}

        def target() -> None:
            try:
                result_container["value"] = func()
            except Exception as e:
                exception_container["value"] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)

        if thread.is_alive():
            raise ExecutionTimeoutError(
                f"Execution exceeded timeout limit of {timeout_seconds} seconds."
            )

        if "value" in exception_container:
            raise exception_container["value"]

        return result_container.get("value")

    def _sleep_with_cancellation_check(self, execution_id: uuid.UUID, seconds: float) -> None:
        interval = 0.1
        slept = 0.0
        while slept < seconds:
            if self.is_cancelled(execution_id):
                raise CancellationError("Execution cancelled during retry delay.")
            time.sleep(min(interval, seconds - slept))
            slept += interval

    def _finalize_success(
        self,
        execution_id: uuid.UUID,
        context: ExecutionContext,
        started_at: datetime,
        output: Any,
        retries: int
    ) -> Result:
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        plan = context.execution_plan

        with self._lock:
            context.completed_at = completed_at
            self._statuses[execution_id] = ExecutionStatus.SUCCESS

            metrics = ExecutionMetrics(
                duration=duration,
                retries=retries,
                timestamps={"started_at": started_at, "completed_at": completed_at},
                execution_cost=plan.estimated_cost
            )
            self._metrics[execution_id] = metrics

        result = Result.success(
            output=output,
            task_id=plan.task.task_id,
            agent_id=plan.task.metadata.get("agent_id"),
            trace_id=plan.task.metadata.get("trace_id"),
            execution_time_ms=duration * 1000.0,
            started_at=started_at,
            finished_at=completed_at,
            metadata={"execution_id": str(execution_id)}
        )

        self._publish_event("executor.completed", execution_id, plan.plan_id)
        self.logger.info(f"Execution completed successfully. ID: {execution_id}", task_id=plan.task.task_id)
        return result

    def _finalize_failure(
        self,
        execution_id: uuid.UUID,
        context: ExecutionContext,
        started_at: datetime,
        exception: Exception,
        retries: int
    ) -> Result:
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        plan = context.execution_plan

        with self._lock:
            context.completed_at = completed_at
            self._statuses[execution_id] = ExecutionStatus.FAILED

            metrics = ExecutionMetrics(
                duration=duration,
                retries=retries,
                timestamps={"started_at": started_at, "completed_at": completed_at},
                execution_cost=plan.estimated_cost
            )
            self._metrics[execution_id] = metrics

        result = Result.failure(
            errors=[str(exception)],
            task_id=plan.task.task_id,
            agent_id=plan.task.metadata.get("agent_id"),
            trace_id=plan.task.metadata.get("trace_id"),
            execution_time_ms=duration * 1000.0,
            started_at=started_at,
            finished_at=completed_at,
            metadata={"execution_id": str(execution_id)}
        )

        self._publish_event("executor.failed", execution_id, plan.plan_id, error=str(exception))
        self.logger.error(f"Execution failed. ID: {execution_id}. Error: {exception}", task_id=plan.task.task_id)
        return result

    def _finalize_timeout(
        self,
        execution_id: uuid.UUID,
        context: ExecutionContext,
        started_at: datetime,
        exception: Exception,
        retries: int
    ) -> Result:
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        plan = context.execution_plan

        with self._lock:
            context.completed_at = completed_at
            self._statuses[execution_id] = ExecutionStatus.TIMEOUT

            metrics = ExecutionMetrics(
                duration=duration,
                retries=retries,
                timestamps={"started_at": started_at, "completed_at": completed_at},
                execution_cost=plan.estimated_cost
            )
            self._metrics[execution_id] = metrics

        result = Result.timeout(
            errors=[str(exception)],
            task_id=plan.task.task_id,
            agent_id=plan.task.metadata.get("agent_id"),
            trace_id=plan.task.metadata.get("trace_id"),
            execution_time_ms=duration * 1000.0,
            started_at=started_at,
            finished_at=completed_at,
            metadata={"execution_id": str(execution_id)}
        )

        self.logger.error(f"Execution timed out. ID: {execution_id}.", task_id=plan.task.task_id)
        return result

    def _finalize_cancelled(
        self,
        execution_id: uuid.UUID,
        context: ExecutionContext,
        started_at: datetime
    ) -> Result:
        completed_at = datetime.utcnow()
        duration = (completed_at - started_at).total_seconds()
        plan = context.execution_plan

        with self._lock:
            context.completed_at = completed_at
            self._statuses[execution_id] = ExecutionStatus.CANCELLED

            metrics = ExecutionMetrics(
                duration=duration,
                timestamps={"started_at": started_at, "completed_at": completed_at},
                execution_cost=plan.estimated_cost
            )
            self._metrics[execution_id] = metrics

        result = Result.cancel(
            task_id=plan.task.task_id,
            agent_id=plan.task.metadata.get("agent_id"),
            trace_id=plan.task.metadata.get("trace_id"),
            execution_time_ms=duration * 1000.0,
            started_at=started_at,
            finished_at=completed_at,
            metadata={"execution_id": str(execution_id)}
        )

        self.logger.warning(f"Execution cancelled. ID: {execution_id}.", task_id=plan.task.task_id)
        return result

    def _publish_event(self, event_name: str, execution_id: uuid.UUID, plan_id: uuid.UUID, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="Executor",
            payload={
                "event_name": event_name,
                "execution_id": str(execution_id),
                "plan_id": str(plan_id),
                **kwargs
            }
        )
        self.event_bus.publish(event)
