from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import threading
from typing import Any, Dict, List, Optional, Union
import uuid

from core.exceptions import NexusException


class LogValidationError(NexusException):
    """Exception raised when LogEntry structure validation fails."""
    pass


class LogLevel(Enum):
    """Observability log levels for categorizing message severity."""
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Dataclass containing structured logging information.

    Attributes:
        level: Log severity classification.
        message: The descriptive message string.
        log_id: Unique UUID associated with the log entry.
        timestamp: Generation timestamp.
        agent_id: Optional related agent UUID.
        task_id: Optional related task UUID.
        workflow_id: Optional related workflow UUID.
        trace_id: Optional correlation tracking UUID.
        metadata: Extra structured query variables.
        duration_ms: Optional process execution time in milliseconds.
        exception: Optional serialized traceback or exception string.
    """
    level: LogLevel
    message: str
    log_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    agent_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    workflow_id: Optional[uuid.UUID] = None
    trace_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    exception: Optional[str] = None

    def __post_init__(self) -> None:
        """Validates entry values."""
        if not isinstance(self.log_id, uuid.UUID):
            raise LogValidationError("log_id must be a valid UUID.")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise LogValidationError("duration_ms cannot be negative.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the LogEntry structure to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the LogEntry.
        """
        return {
            "log_id": str(self.log_id),
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "task_id": str(self.task_id) if self.task_id else None,
            "workflow_id": str(self.workflow_id) if self.workflow_id else None,
            "trace_id": str(self.trace_id) if self.trace_id else None,
            "message": self.message,
            "metadata": self.metadata.copy(),
            "duration_ms": self.duration_ms,
            "exception": self.exception
        }


class Logger(ABC):
    """Interface defining basic severity logging methods."""

    @abstractmethod
    def trace(self, message: str, **kwargs: Any) -> None:
        """Log at TRACE level."""
        pass

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""
        pass


class StructuredLogger(Logger):
    """Thread-safe Singleton structured logger storing telemetry in memory."""
    _instance: Optional["StructuredLogger"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "StructuredLogger":
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
            self._logs: List[LogEntry] = []
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def add(self, entry: LogEntry) -> None:
        """Adds a LogEntry directly to the log store thread-safely.

        Args:
            entry: LogEntry instance.
        """
        with self._lock:
            self._logs.append(entry)

    def log(
        self,
        level: LogLevel,
        message: str,
        agent_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        workflow_id: Optional[uuid.UUID] = None,
        trace_id: Optional[uuid.UUID] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        exception: Optional[Union[Exception, str]] = None
    ) -> None:
        """Constructs and stores a new log entry.

        Args:
            level: The severity level.
            message: Describing context.
            agent_id: Optional identifier.
            task_id: Optional identifier.
            workflow_id: Optional identifier.
            trace_id: Optional identifier.
            metadata: Structured variables dict.
            duration_ms: Operations execution time.
            exception: Exception class context or traceback string.
        """
        exc_str = None
        if exception is not None:
            exc_str = str(exception) if isinstance(exception, Exception) else exception

        entry = LogEntry(
            level=level,
            message=message,
            agent_id=agent_id,
            task_id=task_id,
            workflow_id=workflow_id,
            trace_id=trace_id,
            metadata=metadata or {},
            duration_ms=duration_ms,
            exception=exc_str
        )
        self.add(entry)

    def trace(self, message: str, **kwargs: Any) -> None:
        """Helper to log TRACE category."""
        self.log(LogLevel.TRACE, message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Helper to log DEBUG category."""
        self.log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Helper to log INFO category."""
        self.log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Helper to log WARNING category."""
        self.log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Helper to log ERROR category."""
        self.log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Helper to log CRITICAL category."""
        self.log(LogLevel.CRITICAL, message, **kwargs)

    def get_logs(self) -> List[LogEntry]:
        """Returns all logs currently stored in memory.

        Returns:
            List[LogEntry]: Copy of logs database.
        """
        with self._lock:
            return list(self._logs)

    def filter(
        self,
        agent_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        workflow_id: Optional[uuid.UUID] = None,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[LogEntry]:
        """Filters logs by multiple matching parameters.

        Args:
            agent_id: Matches agent identifier.
            task_id: Matches task identifier.
            workflow_id: Matches workflow identifier.
            level: Severity categorization level.
            start_time: Log generation min threshold.
            end_time: Log generation max threshold.
            metadata: Checks subset metadata match.

        Returns:
            List[LogEntry]: Matching subset list of LogEntry.
        """
        with self._lock:
            filtered = []
            for entry in self._logs:
                if agent_id is not None and entry.agent_id != agent_id:
                    continue
                if task_id is not None and entry.task_id != task_id:
                    continue
                if workflow_id is not None and entry.workflow_id != workflow_id:
                    continue
                if level is not None and entry.level != level:
                    continue
                if start_time is not None and entry.timestamp < start_time:
                    continue
                if end_time is not None and entry.timestamp > end_time:
                    continue
                if metadata is not None:
                    match = True
                    for k, v in metadata.items():
                        if k not in entry.metadata or entry.metadata[k] != v:
                            match = False
                            break
                    if not match:
                        continue
                filtered.append(entry)
            return filtered

    def search(self, query: str) -> List[LogEntry]:
        """Searches message payloads for substring match (case insensitive).

        Args:
            query: Substring value.

        Returns:
            List[LogEntry]: Matching logs.
        """
        query_lower = query.lower()
        with self._lock:
            return [
                entry for entry in self._logs
                if query_lower in entry.message.lower()
            ]

    def clear(self) -> None:
        """Clears all stored logs."""
        with self._lock:
            self._logs.clear()

    def count(self) -> int:
        """Returns stored logs count.

        Returns:
            int: Number of logs.
        """
        with self._lock:
            return len(self._logs)

    def statistics(self) -> Dict[str, Any]:
        """Aggregates log counts and operational metrics.

        Returns:
            Dict[str, Any]: Statistics dictionary summary.
        """
        with self._lock:
            counts = {level.value: 0 for level in LogLevel}
            durations = []
            exception_count = 0

            for entry in self._logs:
                counts[entry.level.value] += 1
                if entry.duration_ms is not None:
                    durations.append(entry.duration_ms)
                if entry.exception is not None:
                    exception_count += 1

            total = len(self._logs)
            avg_duration = sum(durations) / len(durations) if durations else 0.0

            return {
                "total_count": total,
                "by_level": counts,
                "average_duration_ms": avg_duration,
                "exception_count": exception_count
            }

    def export_dict(self) -> List[Dict[str, Any]]:
        """Returns all entries serialized to dictionaries.

        Returns:
            List[Dict[str, Any]]: List of dictionary payloads.
        """
        with self._lock:
            return [entry.to_dict() for entry in self._logs]

    def export_json(self) -> str:
        """Returns JSON string dump of all entries.

        Returns:
            str: JSON representation string.
        """
        with self._lock:
            return json.dumps(self.export_dict(), default=str)
