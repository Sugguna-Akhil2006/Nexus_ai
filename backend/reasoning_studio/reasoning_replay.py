"""Reasoning replay engine — step-by-step and full-run replay of Studio traces."""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from backend.reasoning_studio.models import (
    CapturedReasoningStep,
    ReplaySession,
    ReplayState,
    StudioTrace,
)
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class ReasoningReplay:
    """Manages replay sessions over Studio traces.

    Supports:
    - Full-run replay (all steps returned at once).
    - Step-by-step replay with pause / resume / jump-to.
    - Event publication on replay milestones.
    """

    def __init__(self, trace_store: ReasoningTrace, event_bus: Optional[EventBus] = None) -> None:
        self._store = trace_store
        self._event_bus = event_bus or EventBus()
        self._lock = threading.RLock()
        self._sessions: Dict[str, ReplaySession] = {}

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def create_session(self, studio_trace_id: str) -> ReplaySession:
        """Creates and registers a new replay session for the given trace.

        Args:
            studio_trace_id: ID of the ``StudioTrace`` to replay.

        Returns:
            A fresh ``ReplaySession`` in IDLE state.

        Raises:
            ValueError: If the trace does not exist.
        """
        trace = self._store.get_trace(studio_trace_id)
        if trace is None:
            raise ValueError(f"Studio trace '{studio_trace_id}' not found.")

        session = ReplaySession(
            studio_trace_id=studio_trace_id,
            execution_id=trace.execution_id,
            total_steps=trace.total_steps,
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ReplaySession]:
        """Returns a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    # ------------------------------------------------------------------
    # Control API
    # ------------------------------------------------------------------

    def start(self, session_id: str) -> ReplaySession:
        """Starts or resumes a paused replay session."""
        with self._lock:
            session = self._require_session(session_id)
            if session.state in (ReplayState.IDLE, ReplayState.PAUSED):
                session.state = ReplayState.RUNNING
                session.started_at = session.started_at or datetime.utcnow().isoformat()
                session.paused_at = None
        return session

    def pause(self, session_id: str) -> ReplaySession:
        """Pauses a running replay session."""
        with self._lock:
            session = self._require_session(session_id)
            if session.state == ReplayState.RUNNING:
                session.state = ReplayState.PAUSED
                session.paused_at = datetime.utcnow().isoformat()
        return session

    def jump_to(self, session_id: str, step_index: int) -> ReplaySession:
        """Moves the replay cursor to a specific step index.

        Args:
            session_id: Target session.
            step_index: Zero-based step index to jump to.

        Returns:
            Updated session.

        Raises:
            ValueError: If step_index is out of range.
        """
        with self._lock:
            session = self._require_session(session_id)
            if not (0 <= step_index < session.total_steps):
                raise ValueError(
                    f"step_index {step_index} out of range [0, {session.total_steps - 1}]."
                )
            session.current_step_index = step_index
            session.state = ReplayState.PAUSED
        return session

    # ------------------------------------------------------------------
    # Data retrieval
    # ------------------------------------------------------------------

    def current_step(self, session_id: str) -> Optional[CapturedReasoningStep]:
        """Returns the step at the current cursor position."""
        with self._lock:
            session = self._require_session(session_id)
            trace = self._store.get_trace(session.studio_trace_id)
            if trace and 0 <= session.current_step_index < len(trace.steps):
                return trace.steps[session.current_step_index]
        return None

    def next_step(self, session_id: str) -> Optional[CapturedReasoningStep]:
        """Advances the cursor by one and returns the step.  Returns None if finished."""
        with self._lock:
            session = self._require_session(session_id)
            if session.state != ReplayState.RUNNING:
                return None
            trace = self._store.get_trace(session.studio_trace_id)
            if trace is None:
                return None

            next_idx = session.current_step_index
            if next_idx >= len(trace.steps):
                session.state = ReplayState.COMPLETED
                session.completed_at = datetime.utcnow().isoformat()
                self._publish_replayed(session)
                return None

            step = trace.steps[next_idx]
            session.current_step_index += 1
            return step

    def replay_all(self, studio_trace_id: str) -> List[CapturedReasoningStep]:
        """Returns every step of the trace in order (full replay).

        Publishes ``reasoning.replayed`` on completion.

        Args:
            studio_trace_id: Trace to replay.

        Returns:
            Ordered list of all ``CapturedReasoningStep`` objects.
        """
        trace = self._store.get_trace(studio_trace_id)
        if trace is None:
            raise ValueError(f"Studio trace '{studio_trace_id}' not found.")

        steps = list(trace.steps)
        self._event_bus.publish(Event(
            event_type=EventType.REASONING_REPLAYED,
            priority=EventPriority.NORMAL,
            payload={
                "studio_trace_id": studio_trace_id,
                "steps_replayed": len(steps),
            },
        ))
        return steps

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _require_session(self, session_id: str) -> ReplaySession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError(f"Replay session '{session_id}' not found.")
        return session

    def _publish_replayed(self, session: ReplaySession) -> None:
        self._event_bus.publish(Event(
            event_type=EventType.REASONING_REPLAYED,
            priority=EventPriority.NORMAL,
            payload={
                "session_id": session.session_id,
                "studio_trace_id": session.studio_trace_id,
                "total_steps": session.total_steps,
            },
        ))
