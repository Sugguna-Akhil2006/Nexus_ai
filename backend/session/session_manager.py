"""Session manager coordinating active sessions, checkpoints, timelines, and developer consoles."""

import threading
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.session.models import (
    SessionModel,
    SessionSummaryModel,
    CheckpointModel,
    CheckpointType,
    Decision,
    DecisionType,
    WorkspaceMemoryModel,
    ProjectContextModel,
    ReasoningHistoryModel,
)
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.project_context import ProjectContext
from backend.session.reasoning_history import ReasoningHistory
from backend.session.checkpoint_manager import CheckpointManager
from backend.session.conversation_timeline import ConversationTimeline
from backend.session.decision_tracker import DecisionTracker
from backend.session.context_rebuilder import ContextRebuilder
from backend.session.session_summary import SessionSummary
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class SessionInstance:
    """Individual active Session wrapper containing all coordinate managers."""

    def __init__(self, model: SessionModel) -> None:
        self.model = model
        self.workspace_memory = WorkspaceMemory(model.workspace_memory)
        self.project_context = ProjectContext(model.project_context)
        self.reasoning_history = ReasoningHistory(model.reasoning_history)
        self.timeline = ConversationTimeline(model.timeline)
        self.checkpoint_manager = CheckpointManager(
            self.workspace_memory,
            self.project_context,
            self.reasoning_history,
            model.checkpoints
        )
        self.decision_tracker = DecisionTracker(self.project_context)
        self.rebuilder = ContextRebuilder(self.workspace_memory, self.project_context)
        self.summary_generator = SessionSummary(
            self.workspace_memory,
            self.project_context,
            self.reasoning_history
        )

    def to_model(self) -> SessionModel:
        """Serializes current states of all managers back to a SessionModel."""
        self.model.workspace_memory = self.workspace_memory.get_snapshot()
        self.model.project_context = self.project_context.get_snapshot()
        self.model.reasoning_history = self.reasoning_history.get_snapshot()
        self.model.checkpoints = self.checkpoint_manager.get_checkpoints()
        self.model.timeline = self.timeline.get_events()
        return self.model


class SessionManager:
    """Thread-safe facade managing the lifecycle of AI developer sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionInstance] = {}
        self._active_session_id: Optional[str] = None
        self._lock = threading.RLock()
        self._event_bus = EventBus()

    def create_session(self, name: str) -> SessionInstance:
        """Creates a new session, sets it active, and publishes session.created."""
        with self._lock:
            model = SessionModel(name=name)
            instance = SessionInstance(model)
            self._sessions[model.session_id] = instance
            self._active_session_id = model.session_id

            instance.timeline.record_event(
                event_type="session.created",
                description=f"Session '{name}' created."
            )

            # Publish event
            event = Event(
                event_type=EventType.SESSION_CREATED,
                priority=EventPriority.NORMAL,
                payload={
                    "session_id": model.session_id,
                    "name": name,
                    "created_at": model.created_at
                }
            )
            self._event_bus.publish(event)
            return instance

    def get_session(self, session_id: str) -> SessionInstance:
        """Retrieves a session instance by ID."""
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session '{session_id}' not found.")
            return self._sessions[session_id]

    def get_active_session(self) -> Optional[SessionInstance]:
        """Returns the currently active session instance."""
        with self._lock:
            if not self._active_session_id:
                return None
            return self._sessions.get(self._active_session_id)

    def restore_session(self, session_id: str) -> SessionInstance:
        """Restores a session, marks it active, and publishes session.restored."""
        with self._lock:
            instance = self.get_session(session_id)
            self._active_session_id = session_id
            instance.model.restored_at = datetime.utcnow().isoformat()

            instance.timeline.record_event(
                event_type="session.restored",
                description=f"Session '{instance.model.name}' restored."
            )

            # Publish event
            event = Event(
                event_type=EventType.SESSION_RESTORED,
                priority=EventPriority.NORMAL,
                payload={
                    "session_id": session_id,
                    "restored_at": instance.model.restored_at
                }
            )
            self._event_bus.publish(event)
            return instance

    def checkpoint_session(
        self,
        session_id: str,
        checkpoint_type: CheckpointType,
        description: str = ""
    ) -> CheckpointModel:
        """Triggers a checkpoint snapshot for a specific session."""
        with self._lock:
            instance = self.get_session(session_id)
            checkpoint = instance.checkpoint_manager.create_checkpoint(
                checkpoint_type=checkpoint_type,
                description=description
            )
            instance.timeline.record_event(
                event_type="checkpoint.created",
                description=f"Checkpoint created: {checkpoint_type.value} - {description}",
                payload={"checkpoint_id": checkpoint.checkpoint_id}
            )
            return checkpoint

    def update_workspace_status(
        self,
        session_id: str,
        current_project: Optional[str] = None,
        objective: Optional[str] = None,
        add_file: Optional[str] = None,
        add_task: Optional[str] = None,
        remove_task: Optional[str] = None
    ) -> WorkspaceMemoryModel:
        """Updates components of workspace memory and publishes workspace.updated."""
        with self._lock:
            instance = self.get_session(session_id)
            if current_project is not None:
                instance.workspace_memory.update_project(current_project)
            if objective is not None:
                instance.workspace_memory.set_objective(objective)
            if add_file is not None:
                instance.workspace_memory.add_recent_file(add_file)
            if add_task is not None:
                instance.workspace_memory.add_pending_task(add_task)
            if remove_task is not None:
                instance.workspace_memory.remove_pending_task(remove_task)

            snapshot = instance.workspace_memory.get_snapshot()

            # Publish event
            event = Event(
                event_type=EventType.WORKSPACE_UPDATED,
                priority=EventPriority.NORMAL,
                payload={
                    "session_id": session_id,
                    "current_project": snapshot.current_project,
                    "current_objective": snapshot.current_objective
                }
            )
            self._event_bus.publish(event)
            return snapshot

    # ------------------------------------------------------------------
    # Developer Console APIs
    # ------------------------------------------------------------------

    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """Returns a list of metadata for all registered sessions."""
        with self._lock:
            return [
                {
                    "session_id": s_id,
                    "name": inst.model.name,
                    "created_at": inst.model.created_at,
                    "restored_at": inst.model.restored_at,
                    "is_active": s_id == self._active_session_id
                }
                for s_id, inst in self._sessions.items()
            ]

    def get_workspace_memory_display(self, session_id: str) -> Dict[str, Any]:
        """Provides display details for workspace memory console tab."""
        with self._lock:
            instance = self.get_session(session_id)
            return instance.workspace_memory.get_snapshot().model_dump()

    def get_recent_decisions_display(self, session_id: str) -> List[Dict[str, Any]]:
        """Provides display details for recent decisions console tab."""
        with self._lock:
            instance = self.get_session(session_id)
            decisions = instance.decision_tracker.get_all_decisions()
            return [d.model_dump() for d in decisions]

    def get_reasoning_timeline_display(self, session_id: str) -> List[Dict[str, Any]]:
        """Provides timeline display details including reasoning steps and timeline events."""
        with self._lock:
            instance = self.get_session(session_id)
            timeline_events = instance.timeline.get_events()
            reasoning = instance.reasoning_history.get_snapshot()

            combined = []
            for t_ev in timeline_events:
                combined.append({
                    "type": "timeline_event",
                    "timestamp": t_ev.timestamp,
                    "event_type": t_ev.event_type,
                    "description": t_ev.description,
                })
            for r_step in reasoning.reasoning_steps:
                combined.append({
                    "type": "reasoning_step",
                    "timestamp": r_step.timestamp,
                    "description": r_step.description,
                    "confidence": r_step.confidence,
                })

            combined.sort(key=lambda x: x["timestamp"])
            return combined

    def get_checkpoint_history_display(self, session_id: str) -> List[Dict[str, Any]]:
        """Provides display details for checkpoints console tab."""
        with self._lock:
            instance = self.get_session(session_id)
            checkpoints = instance.checkpoint_manager.get_checkpoints()
            return [
                {
                    "checkpoint_id": cp.checkpoint_id,
                    "timestamp": cp.timestamp,
                    "checkpoint_type": cp.checkpoint_type.value,
                    "description": cp.description,
                }
                for cp in checkpoints
            ]
