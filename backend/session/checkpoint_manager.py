"""Checkpoint manager creating and restoring session state snapshots."""

import threading
from typing import List, Optional
from backend.session.models import CheckpointModel, CheckpointType
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.project_context import ProjectContext
from backend.session.reasoning_history import ReasoningHistory
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class CheckpointManager:
    """Manages creation, retrieval, and restoration of session state checkpoints."""

    def __init__(
        self,
        workspace_memory: WorkspaceMemory,
        project_context: ProjectContext,
        reasoning_history: ReasoningHistory,
        checkpoints_list: Optional[List[CheckpointModel]] = None
    ) -> None:
        self.workspace_memory = workspace_memory
        self.project_context = project_context
        self.reasoning_history = reasoning_history
        self._checkpoints = checkpoints_list if checkpoints_list is not None else []
        self._lock = threading.RLock()
        self._event_bus = EventBus()

    def create_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        description: str = ""
    ) -> CheckpointModel:
        """Saves current state snapshot, appends to history, and publishes event."""
        with self._lock:
            checkpoint = CheckpointModel(
                checkpoint_type=checkpoint_type,
                workspace_memory=self.workspace_memory.get_snapshot(),
                project_context=self.project_context.get_snapshot(),
                reasoning_history=self.reasoning_history.get_snapshot(),
                description=description
            )
            self._checkpoints.append(checkpoint)

            # Publish event
            event = Event(
                event_type=EventType.CHECKPOINT_CREATED,
                priority=EventPriority.NORMAL,
                payload={
                    "checkpoint_id": checkpoint.checkpoint_id,
                    "checkpoint_type": checkpoint_type.value,
                    "description": description
                }
            )
            self._event_bus.publish(event)

            return checkpoint

    def get_checkpoints(self) -> List[CheckpointModel]:
        """Returns all checkpoints."""
        with self._lock:
            return list(self._checkpoints)

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """Restores memory, context, and reasoning states from target checkpoint."""
        with self._lock:
            target = None
            for cp in self._checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    target = cp
                    break
            if not target:
                raise ValueError(f"Checkpoint '{checkpoint_id}' not found.")

            self.workspace_memory.load_snapshot(target.workspace_memory)
            self.project_context.load_snapshot(target.project_context)
            self.reasoning_history.load_snapshot(target.reasoning_history)
