"""Conversation timeline tracking interactions and session lifecycle events."""

import threading
from typing import Any, Dict, List, Optional
from backend.session.models import SessionTimelineEvent


class ConversationTimeline:
    """Thread-safe event sequence representing session timeline history."""

    def __init__(self, events_list: Optional[List[SessionTimelineEvent]] = None) -> None:
        self._events = events_list if events_list is not None else []
        self._lock = threading.RLock()

    def record_event(self, event_type: str, description: str, payload: Optional[Dict[str, Any]] = None) -> SessionTimelineEvent:
        """Appends a new timeline event."""
        with self._lock:
            event = SessionTimelineEvent(
                event_type=event_type,
                description=description,
                payload=payload or {}
            )
            self._events.append(event)
            return event

    def get_events(self) -> List[SessionTimelineEvent]:
        """Returns all timeline events."""
        with self._lock:
            return list(self._events)
