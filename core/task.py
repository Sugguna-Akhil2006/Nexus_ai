from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
import uuid


class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Task:
    """Represents a task to be executed by the agent."""

    def __init__(
        self,
        task_id: Optional[uuid.UUID] = None,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.task_id = task_id or uuid.uuid4()
        self.description = description
        self.metadata = metadata or {}
        self.status = TaskStatus.PENDING
        self.result = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_status(self, status: TaskStatus, result: Optional[Any] = None) -> None:
        """Update the task status and record results."""
        self.status = status
        if result is not None:
            self.result = result
        self.updated_at = datetime.utcnow()
