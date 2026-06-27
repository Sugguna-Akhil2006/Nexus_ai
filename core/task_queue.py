from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading
from typing import Any, Dict, List, Optional, Tuple
import uuid

from core.exceptions import NexusException
from core.task import Task


class QueueError(NexusException):
    """Base exception for all TaskQueue errors."""
    pass


class QueueFullError(QueueError):
    """Raised when enqueuing to a queue at maximum capacity."""
    pass


class DuplicateTaskError(QueueError):
    """Raised when enqueuing a task already present in the queue."""
    pass


class TaskNotFoundError(QueueError):
    """Raised when a specific task is not found in the queue."""
    pass


class QueueValidationError(QueueError):
    """Raised when queue validation or deserialization fails."""
    pass


class QueuePriority(Enum):
    """Priority weights for sorting queue items."""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    SYSTEM = "SYSTEM"


@dataclass
class QueueItem:
    """Represents a wrapped task inside the priority queue.

    Attributes:
        task: The underlying Task object.
        priority: Priority of this item.
        queue_id: Unique identifier for this queue item.
        created_at: Datetime stamp when the task was enqueued.
        scheduled_at: Optional datetime stamp for future scheduled run.
        started_at: Optional timestamp when processing started.
        finished_at: Optional timestamp when processing finished.
        retry_count: Count of retries for this task.
        worker_id: Optional string identifying the execution worker.
        metadata: Metadata key-value map.
    """
    task: Task
    priority: QueuePriority = QueuePriority.NORMAL
    queue_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    retry_count: int = 0
    worker_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Runs basic validation rule checks."""
        if not isinstance(self.queue_id, uuid.UUID):
            raise QueueValidationError("queue_id must be a valid UUID.")
        if self.retry_count < 0:
            raise QueueValidationError("retry_count cannot be negative.")

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the QueueItem attributes to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary payload representing this QueueItem.
        """
        return {
            "queue_id": str(self.queue_id),
            "task": {
                "task_id": str(self.task.task_id),
                "description": self.task.description,
                "status": self.task.status.value,
                "metadata": self.task.metadata.copy(),
            },
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "retry_count": self.retry_count,
            "worker_id": self.worker_id,
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueueItem":
        """Deserializes a QueueItem from a dictionary.

        Args:
            data: Serialization source dictionary.

        Returns:
            QueueItem: Reconstructed instance.

        Raises:
            QueueValidationError: If mandatory fields are missing or wrong format.
        """
        try:
            task_data = data["task"]
            task = Task(
                task_id=uuid.UUID(task_data["task_id"]),
                description=task_data["description"],
                metadata=task_data.get("metadata", {}).copy()
            )

            scheduled_at_val = data.get("scheduled_at")
            started_at_val = data.get("started_at")
            finished_at_val = data.get("finished_at")

            return cls(
                task=task,
                priority=QueuePriority(data.get("priority", "NORMAL")),
                queue_id=uuid.UUID(data["queue_id"]) if "queue_id" in data else uuid.uuid4(),
                created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
                scheduled_at=datetime.fromisoformat(scheduled_at_val) if scheduled_at_val else None,
                started_at=datetime.fromisoformat(started_at_val) if started_at_val else None,
                finished_at=datetime.fromisoformat(finished_at_val) if finished_at_val else None,
                retry_count=int(data.get("retry_count", 0)),
                worker_id=data.get("worker_id"),
                metadata=data.get("metadata", {}).copy(),
            )
        except Exception as e:
            raise QueueValidationError(f"Invalid QueueItem dictionary structure: {e}") from e


class TaskQueue:
    """Thread-safe Singleton priority task queue for scheduling and execution."""
    _instance: Optional["TaskQueue"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "TaskQueue":
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
            self._items: List[Tuple[QueueItem, int]] = []
            self._max_capacity: Optional[int] = None
            self._sequence_counter: int = 0
            self._lock: threading.RLock = threading.RLock()
            self._statistics: Dict[str, Any] = {
                "total_enqueued": 0,
                "total_dequeued": 0,
                "total_removed": 0
            }
            self._initialized = True

    def _priority_value(self, priority: QueuePriority) -> int:
        mapping = {
            QueuePriority.SYSTEM: 0,
            QueuePriority.CRITICAL: 1,
            QueuePriority.HIGH: 2,
            QueuePriority.NORMAL: 3,
            QueuePriority.LOW: 4
        }
        return mapping.get(priority, 3)

    @property
    def max_capacity(self) -> Optional[int]:
        """Gets the maximum capacity limit of the task queue."""
        with self._lock:
            return self._max_capacity

    @max_capacity.setter
    def max_capacity(self, value: Optional[int]) -> None:
        """Sets the maximum capacity limit of the task queue."""
        with self._lock:
            if value is not None and value < 0:
                raise QueueValidationError("Queue capacity limit cannot be negative.")
            self._max_capacity = value

    def enqueue(
        self,
        task: Task,
        priority: QueuePriority = QueuePriority.NORMAL,
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueueItem:
        """Enqueues a task into the priority queue thread-safely.

        Args:
            task: The Task instance to schedule.
            priority: Sorting execution priority.
            scheduled_at: Execution scheduled time limit.
            metadata: Structured tracking values.

        Returns:
            QueueItem: The created queue wrapper.

        Raises:
            QueueFullError: If capacity threshold is reached.
            DuplicateTaskError: If task.task_id is already in the queue.
        """
        with self._lock:
            if self._max_capacity is not None and len(self._items) >= self._max_capacity:
                raise QueueFullError("Queue capacity limit reached.")

            if any(item.task.task_id == task.task_id for item, _ in self._items):
                raise DuplicateTaskError(
                    f"Task ID '{task.task_id}' is already registered in the queue."
                )

            self._sequence_counter += 1
            queue_item = QueueItem(
                task=task,
                priority=priority,
                scheduled_at=scheduled_at,
                metadata=metadata or {}
            )
            self._items.append((queue_item, self._sequence_counter))
            self._statistics["total_enqueued"] += 1
            return queue_item

    def dequeue(self) -> Optional[QueueItem]:
        """Pops the highest priority task from the queue.

        Maintains stable FIFO order for tasks within the same priority level.

        Returns:
            Optional[QueueItem]: The next QueueItem, or None if empty.
        """
        with self._lock:
            if not self._items:
                return None

            self._items.sort(
                key=lambda item: (self._priority_value(item[0].priority), item[1])
            )
            queue_item, _ = self._items.pop(0)
            queue_item.started_at = datetime.utcnow()
            self._statistics["total_dequeued"] += 1
            return queue_item

    def peek(self) -> Optional[QueueItem]:
        """Peeks at the next highest priority task without removing it.

        Returns:
            Optional[QueueItem]: The next QueueItem, or None if empty.
        """
        with self._lock:
            if not self._items:
                return None

            self._items.sort(
                key=lambda item: (self._priority_value(item[0].priority), item[1])
            )
            return self._items[0][0]

    def remove(self, task_id: uuid.UUID) -> Optional[QueueItem]:
        """Removes a task from the queue by its unique task_id.

        Args:
            task_id: The UUID of the task.

        Returns:
            Optional[QueueItem]: The removed QueueItem, or None if not found.
        """
        with self._lock:
            found_idx = -1
            for idx, (item, _) in enumerate(self._items):
                if item.task.task_id == task_id:
                    found_idx = idx
                    break

            if found_idx == -1:
                return None

            item, _ = self._items.pop(found_idx)
            self._statistics["total_removed"] += 1
            return item

    def clear(self) -> None:
        """Clears all tasks and statistics from the queue."""
        with self._lock:
            self._items.clear()
            self._sequence_counter = 0
            self._statistics = {
                "total_enqueued": 0,
                "total_dequeued": 0,
                "total_removed": 0
            }

    def count(self) -> int:
        """Returns the current number of tasks in the queue.

        Returns:
            int: Number of queued tasks.
        """
        with self._lock:
            return len(self._items)

    def is_empty(self) -> bool:
        """Checks if the queue contains no tasks.

        Returns:
            bool: True if empty, False otherwise.
        """
        with self._lock:
            return len(self._items) == 0

    def contains(self, task_id: uuid.UUID) -> bool:
        """Checks if a specific task ID exists in the queue.

        Args:
            task_id: UUID associated with the task.

        Returns:
            bool: True if task exists, False otherwise.
        """
        with self._lock:
            return any(item.task.task_id == task_id for item, _ in self._items)

    def list_tasks(self) -> List[Task]:
        """Lists all tasks currently in the queue, ordered by queue index.

        Returns:
            List[Task]: Copy list of tasks in the queue.
        """
        with self._lock:
            return [item[0].task for item in self._items]

    def statistics(self) -> Dict[str, Any]:
        """Aggregates queue size and historical metrics summary.

        Returns:
            Dict[str, Any]: Statistics summary dictionary.
        """
        with self._lock:
            counts = {p.value: 0 for p in QueuePriority}
            for item, _ in self._items:
                counts[item.priority.value] += 1

            return {
                "current_size": len(self._items),
                "max_capacity": self._max_capacity,
                "total_enqueued": self._statistics["total_enqueued"],
                "total_dequeued": self._statistics["total_dequeued"],
                "total_removed": self._statistics["total_removed"],
                "by_priority": counts
            }
