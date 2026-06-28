from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional

from backend.runtime.exceptions import NexusException


class ResultValidationError(NexusException):
    """Exception raised when Result validation rules are violated."""
    pass


class ResultStatus(Enum):
    """Enums representing the execution outcome status of operations."""
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    RETRY = "RETRY"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Result:
    """Immutable, standardized outcome container for all operations in Nexus Core.

    Attributes:
        status: The execution status of the operation.
        result_id: Unique UUID identifier for this result instance.
        task_id: Optional correlation UUID representing the task.
        agent_id: Optional correlation UUID representing the agent.
        trace_id: Optional correlation UUID for tracing context.
        execution_time_ms: Time duration in milliseconds.
        started_at: Timestamp when execution started.
        finished_at: Timestamp when execution completed.
        output: Any execution result data.
        warnings: List of warning strings.
        errors: List of error strings.
        metadata: Custom runtime metadata.
    """
    status: ResultStatus
    result_id: uuid.UUID = field(default_factory=uuid.uuid4)
    task_id: Optional[uuid.UUID] = None
    agent_id: Optional[uuid.UUID] = None
    trace_id: Optional[uuid.UUID] = None
    execution_time_ms: float = 0.0
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    output: Any = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Runs validation checks on construction to preserve invariants."""
        # Convert lists and dicts to immutable tuples/frozendicts/copies if we want full immutability,
        # but since standard dataclass frozen=True raises errors on assignment,
        # copying lists during validation or post_init is enough.
        # We must use object.__setattr__ to modify dataclass fields because it's frozen.
        object.__setattr__(self, "warnings", list(self.warnings))
        object.__setattr__(self, "errors", list(self.errors))
        object.__setattr__(self, "metadata", dict(self.metadata))
        self.validate()

    def validate(self) -> None:
        """Validates the state of the Result object.

        Raises:
            ResultValidationError: If validation fails.
        """
        if not isinstance(self.result_id, uuid.UUID):
            raise ResultValidationError("result_id must be a valid UUID.")

        if self.execution_time_ms < 0:
            raise ResultValidationError("execution_time_ms cannot be negative.")

        if self.finished_at and self.finished_at < self.started_at:
            raise ResultValidationError("finished_at cannot be earlier than started_at.")

        if self.status in (ResultStatus.SUCCESS, ResultStatus.WARNING):
            if self.errors:
                raise ResultValidationError(
                    f"Result with status {self.status.value} cannot have errors."
                )

        if self.status in (ResultStatus.FAILURE, ResultStatus.TIMEOUT, ResultStatus.RETRY):
            if not self.errors:
                raise ResultValidationError(
                    f"Result with status {self.status.value} must contain errors."
                )

    def is_success(self) -> bool:
        """Checks if the status indicates a successful execution.

        Returns:
            bool: True if status is SUCCESS, PARTIAL_SUCCESS, or WARNING.
        """
        return self.status in (ResultStatus.SUCCESS, ResultStatus.PARTIAL_SUCCESS, ResultStatus.WARNING)

    def is_failure(self) -> bool:
        """Checks if the status indicates a failed execution.

        Returns:
            bool: True if status is FAILURE, TIMEOUT, CANCELLED, or RETRY.
        """
        return self.status in (ResultStatus.FAILURE, ResultStatus.TIMEOUT, ResultStatus.CANCELLED, ResultStatus.RETRY)

    def has_warnings(self) -> bool:
        """Checks if the result contains warnings.

        Returns:
            bool: True if warnings list is not empty.
        """
        return len(self.warnings) > 0

    def duration(self) -> float:
        """Returns duration of the execution in seconds.

        Returns:
            float: Time in seconds.
        """
        if self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return self.execution_time_ms / 1000.0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Result structure to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the Result.
        """
        return {
            "result_id": str(self.result_id),
            "task_id": str(self.task_id) if self.task_id else None,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "status": self.status.value,
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "output": self.output,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Result":
        """Deserializes the Result structure from a dictionary.

        Args:
            data: The dictionary container.

        Returns:
            Result: Newly created Result object.

        Raises:
            ResultValidationError: If deserialization fails or values are invalid.
        """
        try:
            finished_at_val = data.get("finished_at")
            return cls(
                result_id=uuid.UUID(data["result_id"]) if "result_id" in data else uuid.uuid4(),
                task_id=uuid.UUID(data["task_id"]) if data.get("task_id") else None,
                agent_id=uuid.UUID(data["agent_id"]) if data.get("agent_id") else None,
                trace_id=uuid.UUID(data["trace_id"]) if data.get("trace_id") else None,
                status=ResultStatus(data["status"]),
                execution_time_ms=float(data.get("execution_time_ms", 0.0)),
                started_at=datetime.fromisoformat(data["started_at"]) if "started_at" in data else datetime.utcnow(),
                finished_at=datetime.fromisoformat(finished_at_val) if finished_at_val else None,
                output=data.get("output"),
                warnings=list(data.get("warnings", [])),
                errors=list(data.get("errors", [])),
                metadata=data.get("metadata", {}).copy(),
            )
        except Exception as e:
            raise ResultValidationError(f"Invalid Result dictionary structure: {e}") from e

    def copy(self) -> "Result":
        """Creates a deep copy/clone of the Result instance.

        Returns:
            Result: Cloned Result.
        """
        return Result(
            status=self.status,
            result_id=self.result_id,
            task_id=self.task_id,
            agent_id=self.agent_id,
            trace_id=self.trace_id,
            execution_time_ms=self.execution_time_ms,
            started_at=self.started_at,
            finished_at=self.finished_at,
            output=self.output,
            warnings=list(self.warnings),
            errors=list(self.errors),
            metadata=self.metadata.copy(),
        )

    @classmethod
    def success(
        cls,
        output: Any,
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None
    ) -> "Result":
        """Constructs a successful Result instance.

        Args:
            output: Success payload.
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.
            warnings: Optional list of warning strings.

        Returns:
            Result: Success outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.SUCCESS,
            output=output,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=warnings or [],
            errors=[]
        )

    @classmethod
    def failure(
        cls,
        errors: List[str],
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        output: Any = None
    ) -> "Result":
        """Constructs a failed Result instance.

        Args:
            errors: List of error descriptions (must not be empty).
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.
            output: Optional failure payload.

        Returns:
            Result: Failed outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.FAILURE,
            output=output,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=[],
            errors=errors
        )

    @classmethod
    def warning(
        cls,
        output: Any,
        warnings: List[str],
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Result":
        """Constructs a successful Result instance that contains warnings.

        Args:
            output: Success payload.
            warnings: List of warning descriptions.
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.

        Returns:
            Result: Warning outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.WARNING,
            output=output,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=warnings,
            errors=[]
        )

    @classmethod
    def timeout(
        cls,
        errors: List[str],
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Result":
        """Constructs a timeout Result instance.

        Args:
            errors: List of timeout error descriptions.
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.

        Returns:
            Result: Timeout outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.TIMEOUT,
            output=None,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=[],
            errors=errors
        )

    @classmethod
    def retry(
        cls,
        errors: List[str],
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Result":
        """Constructs a retry-request Result instance.

        Args:
            errors: List of failure/retry error descriptions.
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.

        Returns:
            Result: Retry outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.RETRY,
            output=None,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=[],
            errors=errors
        )

    @classmethod
    def cancel(
        cls,
        task_id: Optional[uuid.UUID] = None,
        agent_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        execution_time_ms: float = 0.0,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> "Result":
        """Constructs a cancelled Result instance.

        Args:
            task_id: Optional related task UUID.
            agent_id: Optional related agent UUID.
            trace_id: Optional tracking UUID.
            execution_time_ms: Processing duration in ms.
            started_at: Execution start timestamp.
            finished_at: Execution completion timestamp.
            metadata: Custom metadata dictionary.

        Returns:
            Result: Cancelled outcome Result.
        """
        now = datetime.utcnow()
        return cls(
            status=ResultStatus.CANCELLED,
            output=None,
            task_id=task_id,
            agent_id=agent_id,
            trace_id=trace_id,
            execution_time_ms=execution_time_ms,
            started_at=started_at or now,
            finished_at=finished_at or now,
            metadata=metadata or {},
            warnings=[],
            errors=[]
        )
