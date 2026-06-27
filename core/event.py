from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from typing import Any, Callable, Dict, List, Optional, Protocol, Set, Tuple, Union
import uuid

from core.exceptions import (
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    EventValidationError,
)


class EventType(Enum):
    """Enums representing the standard event types in the Nexus Core framework."""
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"
    AGENT_REGISTERED = "AGENT_REGISTERED"
    AGENT_UNREGISTERED = "AGENT_UNREGISTERED"
    WORKFLOW_STARTED = "WORKFLOW_STARTED"
    WORKFLOW_COMPLETED = "WORKFLOW_COMPLETED"
    WORKFLOW_FAILED = "WORKFLOW_FAILED"
    MEMORY_UPDATED = "MEMORY_UPDATED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DOCUMENT_PARSED = "DOCUMENT_PARSED"
    EMBEDDING_CREATED = "EMBEDDING_CREATED"
    SEARCH_COMPLETED = "SEARCH_COMPLETED"
    SYSTEM_EVENT = "SYSTEM_EVENT"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    CUSTOM_EVENT = "CUSTOM_EVENT"


class EventPriority(Enum):
    """Event priority levels determining execution order."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventStatus(Enum):
    """Runtime statuses of events inside the EventBus."""
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class Event:
    """Dataclass representing a standard event object in the system.

    Attributes:
        event_type: The Type class of the event.
        priority: The priority weight of the event.
        status: The current lifecycle state of the event.
        event_id: Unique UUID identifier.
        correlation_id: Correlation UUID identifier for workflow tracking.
        created_at: Creation timestamp.
        processed_at: Final processing timestamp.
        source: The originating component name.
        target: The target component name (empty if broadcast).
        payload: Custom parameter values dictionary.
        metadata: Tracking metadata dict.
    """
    event_type: EventType
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    correlation_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    source: str = ""
    target: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the Event structure to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the Event.
        """
        return {
            "event_id": str(self.event_id),
            "correlation_id": str(self.correlation_id),
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "source": self.source,
            "target": self.target,
            "payload": self.payload.copy(),
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Deserializes the Event structure from a dictionary.

        Args:
            data: The input dictionary.

        Returns:
            Event: Newly instantiated Event.

        Raises:
            EventValidationError: If mandatory fields are missing or malformed.
        """
        try:
            processed_at_val = data.get("processed_at")
            return cls(
                event_type=EventType(data["event_type"]),
                priority=EventPriority(data.get("priority", "NORMAL")),
                status=EventStatus(data.get("status", "PENDING")),
                event_id=uuid.UUID(data["event_id"]) if "event_id" in data else uuid.uuid4(),
                correlation_id=uuid.UUID(data["correlation_id"]) if "correlation_id" in data else uuid.uuid4(),
                created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
                processed_at=datetime.fromisoformat(processed_at_val) if processed_at_val else None,
                source=data.get("source", ""),
                target=data.get("target", ""),
                payload=data.get("payload", {}).copy(),
                metadata=data.get("metadata", {}).copy(),
            )
        except Exception as e:
            raise EventValidationError(f"Malformed Event data payload: {e}") from e

    def copy(self) -> "Event":
        """Generates a shallow copy of the Event instance.

        Returns:
            Event: Cloned Event.
        """
        return Event(
            event_type=self.event_type,
            priority=self.priority,
            status=self.status,
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            created_at=self.created_at,
            processed_at=self.processed_at,
            source=self.source,
            target=self.target,
            payload=self.payload.copy(),
            metadata=self.metadata.copy(),
        )


class EventHandler(Protocol):
    """Protocol for classes acting as Event subscribers."""

    def handle(self, event: Event) -> None:
        """Invoked when a matching event is dispatched.

        Args:
            event: The Event object.
        """
        ...


class EventBus:
    """Thread-safe Singleton EventBus coordinating event delivery."""
    _instance: Optional["EventBus"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "EventBus":
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
            self._subscribers: Dict[Union[EventType, str], List[Tuple[Any, Optional[Callable[[Event], bool]]]]] = {}
            self._queue: List[Tuple[Event, int]] = []
            self._history: List[Event] = []
            self._capabilities: Dict[str, Any] = {}
            self._sequence_counter: int = 0
            self._lock: threading.RLock = threading.RLock()
            self._statistics: Dict[str, Any] = {
                "published_count": 0,
                "dispatched_count": 0,
                "failed_count": 0,
                "by_type": {
                    etype.value: {"published": 0, "dispatched": 0, "failed": 0}
                    for etype in EventType
                }
            }
            self._initialized = True

    def _priority_value(self, priority: EventPriority) -> int:
        mapping = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3
        }
        return mapping.get(priority, 2)

    def _get_handlers_for_event(self, event_type: EventType) -> List[Tuple[Any, Optional[Callable[[Event], bool]]]]:
        handlers = []
        if event_type in self._subscribers:
            handlers.extend(self._subscribers[event_type])
        if "*" in self._subscribers:
            handlers.extend(self._subscribers["*"])
        return handlers

    def publish(self, event: Event) -> None:
        """Places an event onto the EventBus queue.

        Args:
            event: The Event instance to publish.
        """
        with self._lock:
            event.status = EventStatus.QUEUED
            self._sequence_counter += 1
            self._queue.append((event, self._sequence_counter))

            self._statistics["published_count"] += 1
            etype_str = event.event_type.value
            if etype_str not in self._statistics["by_type"]:
                self._statistics["by_type"][etype_str] = {
                    "published": 0,
                    "dispatched": 0,
                    "failed": 0
                }
            self._statistics["by_type"][etype_str]["published"] += 1

    def subscribe(
        self,
        event_type: Union[EventType, str],
        handler: Union[EventHandler, Callable[[Event], None]],
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> None:
        """Subscribes a handler to a specific EventType or wildcard pattern.

        Args:
            event_type: The EventType enum or wildcard string "*".
            handler: The handler implementing handle() or a callable.
            filter_func: Optional filtering condition for matching events.

        Raises:
            DuplicateSubscriptionError: If the handler is already subscribed to the event_type.
            EventValidationError: If subscription parameters are invalid.
        """
        if isinstance(event_type, str) and event_type != "*":
            raise EventValidationError("Only specific EventType enums or '*' wildcard are supported.")

        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []

            for registered_handler, _ in self._subscribers[event_type]:
                if registered_handler == handler:
                    raise DuplicateSubscriptionError(
                        f"Handler already subscribed to {event_type}."
                    )

            self._subscribers[event_type].append((handler, filter_func))

    def unsubscribe(
        self,
        event_type: Union[EventType, str],
        handler: Union[EventHandler, Callable[[Event], None]]
    ) -> None:
        """Unsubscribes a handler from the event type.

        Args:
            event_type: The EventType enum or wildcard string "*".
            handler: The handler to remove.

        Raises:
            SubscriptionNotFoundError: If subscription registry entry is missing.
        """
        with self._lock:
            if (
                event_type not in self._subscribers or
                not any(h == handler for h, _ in self._subscribers[event_type])
            ):
                raise SubscriptionNotFoundError(
                    f"Handler is not registered under {event_type}."
                )

            self._subscribers[event_type] = [
                (h, f) for h, f in self._subscribers[event_type] if h != handler
            ]
            if not self._subscribers[event_type]:
                del self._subscribers[event_type]

    def dispatch(self) -> Optional[Event]:
        """Dispatches the next highest priority event from the queue.

        Returns:
            Optional[Event]: The dispatched Event, or None if queue is empty.
        """
        with self._lock:
            if not self._queue:
                return None

            self._queue.sort(
                key=lambda item: (self._priority_value(item[0].priority), item[1])
            )
            event, _ = self._queue.pop(0)

            self._dispatch_single(event)
            return event

    def dispatch_all(self) -> int:
        """Dispatches all pending events in the queue recursively until empty.

        Returns:
            int: The number of events successfully dispatched.
        """
        count = 0
        while True:
            event = self.dispatch()
            if event is None:
                break
            count += 1
        return count

    def _dispatch_single(self, event: Event) -> None:
        event.status = EventStatus.DISPATCHED
        self._statistics["dispatched_count"] += 1
        etype_str = event.event_type.value
        if etype_str not in self._statistics["by_type"]:
            self._statistics["by_type"][etype_str] = {
                "published": 0,
                "dispatched": 0,
                "failed": 0
            }
        self._statistics["by_type"][etype_str]["dispatched"] += 1

        handlers = self._get_handlers_for_event(event.event_type)
        if not handlers:
            event.status = EventStatus.COMPLETED
            event.processed_at = datetime.utcnow()
            self._history.append(event)
            return

        event.status = EventStatus.PROCESSING
        has_failures = False

        for handler, filter_func in handlers:
            if filter_func is not None:
                try:
                    if not filter_func(event):
                        continue
                except Exception as e:
                    has_failures = True
                    self._record_failure(event, handler, e)
                    continue

            try:
                if hasattr(handler, "handle") and callable(handler.handle):
                    handler.handle(event)
                elif callable(handler):
                    handler(event)
                else:
                    raise TypeError(
                        "Handler must implement EventHandler protocol or be a callable."
                    )
            except Exception as e:
                has_failures = True
                self._record_failure(event, handler, e)

        if has_failures:
            event.status = EventStatus.FAILED
        else:
            event.status = EventStatus.COMPLETED

        event.processed_at = datetime.utcnow()
        self._history.append(event)

    def _record_failure(self, event: Event, handler: Any, exception: Exception) -> None:
        self._statistics["failed_count"] += 1
        etype_str = event.event_type.value
        if etype_str not in self._statistics["by_type"]:
            self._statistics["by_type"][etype_str] = {
                "published": 0,
                "dispatched": 0,
                "failed": 0
            }
        self._statistics["by_type"][etype_str]["failed"] += 1

        if "errors" not in event.metadata:
            event.metadata["errors"] = []
        event.metadata["errors"].append({
            "handler": str(handler),
            "error": str(exception),
            "timestamp": datetime.utcnow().isoformat()
        })

    def clear(self) -> None:
        """Resets the EventBus state, clearing subscribers, queues, and statistics."""
        with self._lock:
            self._subscribers.clear()
            self._queue.clear()
            self._history.clear()
            self._capabilities.clear()
            self._sequence_counter = 0
            self._statistics = {
                "published_count": 0,
                "dispatched_count": 0,
                "failed_count": 0,
                "by_type": {
                    etype.value: {"published": 0, "dispatched": 0, "failed": 0}
                    for etype in EventType
                }
            }

    def history(self) -> List[Event]:
        """Returns a snapshot of the processed events history.

        Returns:
            List[Event]: Copy of the history list.
        """
        with self._lock:
            return list(self._history)

    def pending_events(self) -> List[Event]:
        """Returns a list of all currently queued events.

        Returns:
            List[Event]: Copy of the pending event queue.
        """
        with self._lock:
            return [item[0] for item in self._queue]

    def processed_events(self) -> List[Event]:
        """Returns a snapshot of the processed events history.

        Returns:
            List[Event]: Copy of the history list.
        """
        with self._lock:
            return list(self._history)

    def subscriber_count(self, event_type: Optional[Union[EventType, str]] = None) -> int:
        """Returns the subscriber registry entries count.

        Args:
            event_type: Optional filter by specific EventType.

        Returns:
            int: The subscriber count.
        """
        with self._lock:
            if event_type is not None:
                return len(self._subscribers.get(event_type, []))

            unique_handlers = set()
            for handlers_list in self._subscribers.values():
                for handler, _ in handlers_list:
                    try:
                        unique_handlers.add(handler)
                    except TypeError:
                        unique_handlers.add(id(handler))
            return len(unique_handlers)

    def event_count(self) -> int:
        """Returns the number of pending events.

        Returns:
            int: Size of the pending queue.
        """
        with self._lock:
            return len(self._queue)

    def has_subscribers(self, event_type: Optional[EventType] = None) -> bool:
        """Checks if there are registered subscribers.

        Args:
            event_type: Optional EventType category filter.

        Returns:
            bool: True if there are subscribers, False otherwise.
        """
        with self._lock:
            if event_type is not None:
                return len(self._get_handlers_for_event(event_type)) > 0
            return len(self._subscribers) > 0

    def statistics(self) -> Dict[str, Any]:
        """Returns a snapshot copy of the current metrics.

        Returns:
            Dict[str, Any]: Statistics dictionary copy.
        """
        with self._lock:
            return {
                "published_count": self._statistics["published_count"],
                "dispatched_count": self._statistics["dispatched_count"],
                "failed_count": self._statistics["failed_count"],
                "by_type": {
                    k: v.copy() for k, v in self._statistics["by_type"].items()
                }
            }
