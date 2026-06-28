from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger
from backend.execution.planner import ExecutionMode, ExecutionPlan


class DispatchError(NexusException):
    """Base exception for all dispatch-related errors."""
    pass


class DispatchValidationError(DispatchError):
    """Raised when validation of an ExecutionPlan or destination registration fails."""
    pass


class DuplicateTargetError(DispatchError):
    """Raised when registering a target that already exists in the registry."""
    pass


class TargetNotFoundError(DispatchError):
    """Raised when a resolved routing target name is not registered."""
    pass


class DispatchStatus(Enum):
    """Execution dispatch statuses indicating outcome of target routing."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class DispatchResult:
    """Immutable outcome descriptor of an ExecutionPlan routing operation.

    Attributes:
        dispatch_id: Unique UUID identifier.
        plan_id: Related ExecutionPlan plan_id.
        destination: Unique target name identifier where the plan was sent.
        dispatched_at: Creation timestamp.
        status: Routing outcome status.
        metadata: Extra structured query variables.
    """
    dispatch_id: uuid.UUID
    plan_id: Optional[uuid.UUID]
    destination: str
    dispatched_at: datetime
    status: DispatchStatus
    metadata: Dict[str, Any] = field(default_factory=dict)


class DispatchTarget(ABC):
    """Interface defining basic capability for a routing destination."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the unique name of the dispatch target."""
        pass

    @abstractmethod
    def handle_dispatch(self, plan: ExecutionPlan) -> None:
        """Invoked when routing the execution plan to this target.

        Args:
            plan: The ExecutionPlan to process.
        """
        pass


class Dispatcher:
    """Thread-safe Singleton message router managing ExecutionPlan targets."""
    _instance: Optional["Dispatcher"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "Dispatcher":
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
            self._targets: Dict[str, DispatchTarget] = {}
            self._routing_rules: Dict[ExecutionMode, str] = {
                ExecutionMode.IMMEDIATE: "Executor",
                ExecutionMode.ASYNC: "Scheduler",
                ExecutionMode.PARALLEL: "Scheduler",
                ExecutionMode.SCHEDULED: "Scheduler",
                ExecutionMode.DISTRIBUTED: "Distributed"
            }
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def register_target(self, target: DispatchTarget) -> None:
        """Registers a DispatchTarget destination thread-safely.

        Args:
            target: The destination target instance.

        Raises:
            DuplicateTargetError: If name conflicts with an existing target.
            DispatchValidationError: If target structure is invalid.
        """
        if not target or not target.name or not str(target.name).strip():
            raise DispatchValidationError("Invalid dispatch target interface.")

        with self._lock:
            if target.name in self._targets:
                raise DuplicateTargetError(
                    f"Target name '{target.name}' is already registered."
                )
            self._targets[target.name] = target

    def unregister_target(self, target_name: str) -> None:
        """Unregisters a target by name.

        Args:
            target_name: The name of the target.

        Raises:
            TargetNotFoundError: If target is not registered.
        """
        with self._lock:
            if target_name not in self._targets:
                raise TargetNotFoundError(
                    f"Unregistration failed. Target '{target_name}' not found."
                )
            del self._targets[target_name]

    def list_targets(self) -> List[str]:
        """Lists names of all registered target destinations.

        Returns:
            List[str]: List of target names.
        """
        with self._lock:
            return list(self._targets.keys())

    def set_routing_rule(self, mode: ExecutionMode, target_name: str) -> None:
        """Maps an ExecutionMode category to a target destination.

        Args:
            mode: Target ExecutionMode.
            target_name: The name of the registered destination.
        """
        with self._lock:
            self._routing_rules[mode] = target_name

    def resolve_destination(self, plan: ExecutionPlan) -> DispatchTarget:
        """Resolves the target registry destination mapped to plan's execution_mode.

        Args:
            plan: The execution plan.

        Returns:
            DispatchTarget: The resolved target.

        Raises:
            TargetNotFoundError: If destination target configuration is missing.
        """
        with self._lock:
            target_name = self._routing_rules.get(plan.execution_mode)
            if not target_name:
                raise TargetNotFoundError(
                    f"No routing destination configured for mode '{plan.execution_mode.value}'."
                )

            target = self._targets.get(target_name)
            if not target:
                raise TargetNotFoundError(
                    f"Target destination '{target_name}' is not registered."
                )
            return target

    def validate_plan(self, plan: ExecutionPlan) -> None:
        """Validates plan attributes.

        Args:
            plan: The ExecutionPlan.

        Raises:
            DispatchValidationError: If validation fails.
        """
        if not plan:
            raise DispatchValidationError("ExecutionPlan cannot be None.")

        if not getattr(plan, "plan_id", None):
            raise DispatchValidationError("ExecutionPlan has an empty or missing plan_id.")

        if not getattr(plan, "task", None):
            raise DispatchValidationError("ExecutionPlan has an empty or missing task.")

        if not getattr(plan, "execution_mode", None) or not isinstance(plan.execution_mode, ExecutionMode):
            raise DispatchValidationError("ExecutionPlan has an invalid execution_mode.")

    def dispatch(self, plan: ExecutionPlan) -> DispatchResult:
        """Routes the ExecutionPlan to its resolved target destination.

        Args:
            plan: The ExecutionPlan.

        Returns:
            DispatchResult: Dispatch outcome descriptor.

        Raises:
            DispatchValidationError: On plan validation failure.
            DispatchError: On execution/routing runtime failures.
        """
        dispatch_id = uuid.uuid4()
        dispatched_at = datetime.utcnow()
        plan_id = getattr(plan, "plan_id", None)
        task_id = getattr(plan.task, "task_id", None) if plan and getattr(plan, "task", None) else None

        self.logger.info(f"Dispatch started. Plan ID: {plan_id}", task_id=task_id)
        self._publish_event("dispatcher.started", dispatch_id=dispatch_id, plan_id=plan_id)

        try:
            self.validate_plan(plan)
            target = self.resolve_destination(plan)

            self.logger.info(
                f"Resolved target '{target.name}' for Plan ID: {plan_id}",
                task_id=task_id
            )

            # Delegate routing
            target.handle_dispatch(plan)

            result = DispatchResult(
                dispatch_id=dispatch_id,
                plan_id=plan_id,
                destination=target.name,
                dispatched_at=dispatched_at,
                status=DispatchStatus.SUCCESS,
                metadata={"execution_mode": plan.execution_mode.value}
            )

            self._publish_event(
                "dispatcher.completed",
                dispatch_id=dispatch_id,
                plan_id=plan_id,
                status="SUCCESS"
            )
            self.logger.info(
                f"Successful dispatch to target '{target.name}'. Plan ID: {plan_id}",
                task_id=task_id
            )
            return result

        except Exception as e:
            self.logger.error(f"Dispatch error occurred: {e}", task_id=task_id)
            self._publish_event(
                "dispatcher.failed",
                dispatch_id=dispatch_id,
                plan_id=plan_id,
                error=str(e)
            )

            status = (
                DispatchStatus.REJECTED
                if isinstance(e, DispatchValidationError)
                else DispatchStatus.FAILED
            )

            result = DispatchResult(
                dispatch_id=dispatch_id,
                plan_id=plan_id if plan else None,
                destination="Unknown",
                dispatched_at=dispatched_at,
                status=status,
                metadata={"error": str(e)}
            )

            if isinstance(e, DispatchValidationError):
                raise
            raise DispatchError(f"Failed to dispatch plan: {e}") from e

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="Dispatcher",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
