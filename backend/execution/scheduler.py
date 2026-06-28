from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from typing import Any, Dict, List, Optional, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger
from backend.execution.planner import ExecutionPlan


class SchedulerError(NexusException):
    """Base exception for all scheduler-related errors."""
    pass


class ScheduleValidationError(SchedulerError):
    """Raised when schedule parameters or policy validation fails."""
    pass


class DuplicateScheduleError(SchedulerError):
    """Raised when a schedule with a duplicate ID is registered."""
    pass


class ScheduleNotFoundError(SchedulerError):
    """Raised when the specified schedule identifier is not found."""
    pass


class ScheduleStatus(Enum):
    """Lifecycle statuses for execution schedules inside the Scheduler."""
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class RecurrencePolicy:
    """Configuration determining recurring executions of planned tasks.

    Attributes:
        interval: Periodic time gap in seconds between executions.
        cron_expression: Optional cron syntax pattern placeholder.
        max_occurrences: Maximum times to trigger this execution rule.
        end_time: Stop boundary deadline timestamp.
    """
    interval: Optional[float] = None
    cron_expression: Optional[str] = None
    max_occurrences: Optional[int] = None
    end_time: Optional[datetime] = None

    def validate(self) -> None:
        """Validates recurrence configurations.

        Raises:
            ScheduleValidationError: On invalid property entries.
        """
        if self.interval is not None and self.interval <= 0:
            raise ScheduleValidationError("Recurrence interval must be positive.")
        if self.max_occurrences is not None and self.max_occurrences <= 0:
            raise ScheduleValidationError("max_occurrences count must be positive.")


@dataclass
class ScheduleEntry:
    """Wrapper encapsulating execution plan timing, state, and recurrences.

    Attributes:
        schedule_id: Unique UUID associated with the schedule.
        execution_plan: The scheduled ExecutionPlan.
        scheduled_time: Target start execution time.
        created_at: Datetime stamp when the schedule entry was created.
        next_run: Timestamp of the next run (for retries or recurrences).
        recurrence_rule: Optional recurrence policies configuration.
        retry_count: Tracked count of execution retries.
        timeout: Expiry threshold limit in seconds.
        status: The schedule status.
        metadata: Extra structured metadata map.
    """
    schedule_id: uuid.UUID
    execution_plan: ExecutionPlan
    scheduled_time: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    next_run: Optional[datetime] = None
    recurrence_rule: Optional[RecurrencePolicy] = None
    retry_count: int = 0
    timeout: float = 30.0
    status: ScheduleStatus = ScheduleStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validates schedule entries."""
        if not isinstance(self.schedule_id, uuid.UUID):
            raise ScheduleValidationError("schedule_id must be a valid UUID.")
        if self.timeout <= 0:
            raise ScheduleValidationError("timeout limit must be positive.")
        if self.retry_count < 0:
            raise ScheduleValidationError("retry_count cannot be negative.")


class Scheduler:
    """Thread-safe Singleton scheduler coordinating plan timelines and schedules."""
    _instance: Optional["Scheduler"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "Scheduler":
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
            self._schedules: Dict[uuid.UUID, ScheduleEntry] = {}
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def schedule(self, plan: ExecutionPlan) -> ScheduleEntry:
        """Schedules a plan for delayed, immediate, or recurring execution.

        Args:
            plan: The ExecutionPlan.

        Returns:
            ScheduleEntry: The newly created ScheduleEntry.

        Raises:
            ScheduleValidationError: If the scheduling rules or values are invalid.
            SchedulerError: On registration failures.
        """
        if not plan:
            raise ScheduleValidationError("ExecutionPlan cannot be None.")

        task_id = getattr(plan.task, "task_id", None)
        self.logger.info(f"Scheduling started for plan: {plan.plan_id}", task_id=task_id)

        try:
            # Parse scheduled_time
            sched_time_val = plan.metadata.get("scheduled_time")
            if sched_time_val:
                if isinstance(sched_time_val, str):
                    try:
                        scheduled_time = datetime.fromisoformat(sched_time_val)
                    except ValueError as e:
                        raise ScheduleValidationError(f"Invalid scheduled_time string format: {e}") from e
                elif isinstance(sched_time_val, datetime):
                    scheduled_time = sched_time_val
                else:
                    raise ScheduleValidationError("scheduled_time must be a string or datetime.")
            else:
                scheduled_time = datetime.utcnow()

            # Past execution time check
            allow_past = plan.metadata.get("allow_past", False)
            now = datetime.utcnow()
            if not allow_past and scheduled_time < now - timedelta(seconds=2):
                raise ScheduleValidationError(
                    f"Cannot schedule execution in the past: {scheduled_time.isoformat()}"
                )

            # Parse Recurrence Policy
            recurrence_data = plan.metadata.get("recurrence_policy")
            recurrence_rule = None
            if recurrence_data:
                end_time_val = recurrence_data.get("end_time")
                end_time = None
                if end_time_val:
                    if isinstance(end_time_val, str):
                        end_time = datetime.fromisoformat(end_time_val)
                    elif isinstance(end_time_val, datetime):
                        end_time = end_time_val

                recurrence_rule = RecurrencePolicy(
                    interval=recurrence_data.get("interval"),
                    cron_expression=recurrence_data.get("cron_expression"),
                    max_occurrences=recurrence_data.get("max_occurrences"),
                    end_time=end_time
                )
                recurrence_rule.validate()

            schedule_id = uuid.uuid4()
            entry = ScheduleEntry(
                schedule_id=schedule_id,
                execution_plan=plan,
                scheduled_time=scheduled_time,
                next_run=scheduled_time,
                recurrence_rule=recurrence_rule,
                timeout=plan.timeout,
                status=ScheduleStatus.PENDING,
                metadata=plan.metadata.copy()
            )

            with self._lock:
                if schedule_id in self._schedules:
                    raise DuplicateScheduleError(f"Schedule ID '{schedule_id}' is already registered.")
                self._schedules[schedule_id] = entry

            self._publish_event("scheduler.plan.scheduled", schedule_id, plan.plan_id)
            self.logger.info(
                f"Schedule created successfully. ID: {schedule_id}. Plan ID: {plan.plan_id}",
                task_id=task_id
            )
            return entry

        except Exception as e:
            self.logger.error(f"Scheduling error: {e}", task_id=task_id)
            if isinstance(e, ScheduleValidationError):
                raise
            raise SchedulerError(f"Failed to schedule execution plan: {e}") from e

    def cancel(self, schedule_id: Union[uuid.UUID, str]) -> bool:
        """Cancels a scheduled plan execution if it is not completed.

        Args:
            schedule_id: Unique schedule ID identifier.

        Returns:
            bool: True if cancellation succeeded, False otherwise.
        """
        s_id = uuid.UUID(str(schedule_id)) if not isinstance(schedule_id, uuid.UUID) else schedule_id
        with self._lock:
            entry = self._schedules.get(s_id)
            if not entry:
                self.logger.warning(f"Cancellation failed. Schedule ID '{s_id}' not found.")
                return False

            if entry.status in (
                ScheduleStatus.COMPLETED,
                ScheduleStatus.FAILED,
                ScheduleStatus.CANCELLED,
                ScheduleStatus.EXPIRED
            ):
                return False

            entry.status = ScheduleStatus.CANCELLED
            self._publish_event("scheduler.plan.cancelled", s_id, entry.execution_plan.plan_id)
            self.logger.info(f"Cancellation successful. Schedule ID: {s_id}")
            return True

    def reschedule(self, schedule_id: Union[uuid.UUID, str], new_time: datetime) -> ScheduleEntry:
        """Reschedules a pending task schedule to a new target datetime.

        Args:
            schedule_id: Unique schedule ID identifier.
            new_time: The new execution scheduled datetime.

        Returns:
            ScheduleEntry: The updated ScheduleEntry.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
            ScheduleValidationError: If the target datetime is in the past.
            SchedulerError: If the schedule status is completed, failed, or expired.
        """
        s_id = uuid.UUID(str(schedule_id)) if not isinstance(schedule_id, uuid.UUID) else schedule_id
        if not new_time:
            raise ScheduleValidationError("New scheduled time cannot be None.")

        with self._lock:
            entry = self._schedules.get(s_id)
            if not entry:
                raise ScheduleNotFoundError(f"Schedule ID '{s_id}' not found.")

            if entry.status in (
                ScheduleStatus.COMPLETED,
                ScheduleStatus.FAILED,
                ScheduleStatus.EXPIRED
            ):
                raise SchedulerError(
                    f"Rescheduling failed. Current status is '{entry.status.value}'."
                )

            allow_past = entry.metadata.get("allow_past", False)
            now = datetime.utcnow()
            if not allow_past and new_time < now - timedelta(seconds=2):
                raise ScheduleValidationError(
                    f"Cannot reschedule execution to a past time: {new_time.isoformat()}"
                )

            entry.scheduled_time = new_time
            entry.next_run = new_time
            entry.status = ScheduleStatus.PENDING

            self._publish_event("scheduler.plan.rescheduled", s_id, entry.execution_plan.plan_id)
            self.logger.info(f"Rescheduled successfully. ID: {s_id}. Time: {new_time.isoformat()}")
            return entry

    def get(self, schedule_id: Union[uuid.UUID, str]) -> Optional[ScheduleEntry]:
        """Retrieves a ScheduleEntry from the registry by its ID.

        Args:
            schedule_id: Unique schedule UUID.

        Returns:
            Optional[ScheduleEntry]: Match schedule entry object, or None.
        """
        s_id = uuid.UUID(str(schedule_id)) if not isinstance(schedule_id, uuid.UUID) else schedule_id
        with self._lock:
            return self._schedules.get(s_id)

    def list_pending(self) -> List[ScheduleEntry]:
        """Lists all schedule entries that are pending or retrying in the future.

        Returns:
            List[ScheduleEntry]: Pending execution schedules.
        """
        now = datetime.utcnow()
        with self._lock:
            return [
                entry for entry in self._schedules.values()
                if entry.status in (ScheduleStatus.PENDING, ScheduleStatus.RETRYING)
                and entry.next_run is not None and entry.next_run > now
            ]

    def list_ready(self, now: datetime) -> List[ScheduleEntry]:
        """Retrieves and flags ready schedules that have crossed execution boundaries.

        Sets status of ready items to READY and fires planner ready events.

        Args:
            now: Current execution comparison boundary datetime.

        Returns:
            List[ScheduleEntry]: Ready execution schedules.
        """
        with self._lock:
            ready_entries = []
            for entry in self._schedules.values():
                if entry.status in (ScheduleStatus.PENDING, ScheduleStatus.RETRYING):
                    if entry.next_run is not None and entry.next_run <= now:
                        entry.status = ScheduleStatus.READY
                        self._publish_event("scheduler.plan.ready", entry.schedule_id, entry.execution_plan.plan_id)
                        ready_entries.append(entry)
            return ready_entries

    def schedule_retry(self, schedule_id: Union[uuid.UUID, str], delay_seconds: float) -> ScheduleEntry:
        """Schedules a delayed retry attempt for a failed execution plan.

        Args:
            schedule_id: Unique schedule ID identifier.
            delay_seconds: Wait threshold delay in seconds before next retry run.

        Returns:
            ScheduleEntry: The updated ScheduleEntry.

        Raises:
            ScheduleNotFoundError: If the schedule does not exist.
            ScheduleValidationError: If delay is negative.
        """
        s_id = uuid.UUID(str(schedule_id)) if not isinstance(schedule_id, uuid.UUID) else schedule_id
        if delay_seconds < 0:
            raise ScheduleValidationError("Retry delay cannot be negative.")

        with self._lock:
            entry = self._schedules.get(s_id)
            if not entry:
                raise ScheduleNotFoundError(f"Schedule ID '{s_id}' not found.")

            entry.retry_count += 1
            new_run_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
            entry.scheduled_time = new_run_time
            entry.next_run = new_run_time
            entry.status = ScheduleStatus.RETRYING

            self._publish_event(
                "scheduler.plan.retry",
                s_id,
                entry.execution_plan.plan_id,
                retry_count=entry.retry_count
            )
            self.logger.info(
                f"Retry scheduled. ID: {s_id}. Delay: {delay_seconds}s. Count: {entry.retry_count}"
            )
            return entry

    def trigger_recurrence(self, schedule_id: Union[uuid.UUID, str]) -> Optional[datetime]:
        """Calculates recurrence boundaries and schedules the next execution run.

        Args:
            schedule_id: Unique schedule ID identifier.

        Returns:
            Optional[datetime]: Next run datetime, or None if recurrence ended.
        """
        s_id = uuid.UUID(str(schedule_id)) if not isinstance(schedule_id, uuid.UUID) else schedule_id
        with self._lock:
            entry = self._schedules.get(s_id)
            if not entry or not entry.recurrence_rule:
                return None

            rule = entry.recurrence_rule
            now = datetime.utcnow()

            # End Time Check
            if rule.end_time and now >= rule.end_time:
                entry.status = ScheduleStatus.COMPLETED
                return None

            # Max Occurrences Check
            if rule.max_occurrences is not None:
                occurrences = entry.metadata.get("occurrence_count", 0) + 1
                entry.metadata["occurrence_count"] = occurrences
                if occurrences >= rule.max_occurrences:
                    entry.status = ScheduleStatus.COMPLETED
                    return None

            if rule.interval is not None:
                next_run = (entry.next_run or now) + timedelta(seconds=rule.interval)

                if rule.end_time and next_run > rule.end_time:
                    entry.status = ScheduleStatus.COMPLETED
                    return None

                entry.next_run = next_run
                entry.status = ScheduleStatus.PENDING
                self._publish_event("scheduler.plan.rescheduled", s_id, entry.execution_plan.plan_id)
                self.logger.info(
                    f"Recurrence trigger. ID: {s_id}. Next Run: {next_run.isoformat()}"
                )
                return next_run

            return None

    def cleanup_expired(self) -> int:
        """Cleans up expired or timeout-overdue pending schedule entries.

        Sets status of expired items to EXPIRED and fires expiration events.

        Returns:
            int: Number of schedules expired.
        """
        now = datetime.utcnow()
        count = 0
        with self._lock:
            for entry in self._schedules.values():
                if entry.status in (ScheduleStatus.PENDING, ScheduleStatus.RETRYING):
                    # End time constraint
                    if entry.recurrence_rule and entry.recurrence_rule.end_time and entry.recurrence_rule.end_time < now:
                        entry.status = ScheduleStatus.EXPIRED
                        self._publish_event("scheduler.plan.expired", entry.schedule_id, entry.execution_plan.plan_id)
                        self.logger.info(f"Schedule ID '{entry.schedule_id}' expired (reached end_time boundary).")
                        count += 1
                        continue

                    # Timeout constraints
                    if entry.scheduled_time + timedelta(seconds=entry.timeout) < now:
                        entry.status = ScheduleStatus.EXPIRED
                        self._publish_event("scheduler.plan.expired", entry.schedule_id, entry.execution_plan.plan_id)
                        self.logger.info(f"Schedule ID '{entry.schedule_id}' expired (timeout elapsed).")
                        count += 1
            return count

    def _publish_event(self, event_name: str, schedule_id: uuid.UUID, plan_id: uuid.UUID, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="Scheduler",
            payload={
                "event_name": event_name,
                "schedule_id": str(schedule_id),
                "plan_id": str(plan_id),
                **kwargs
            }
        )
        self.event_bus.publish(event)
