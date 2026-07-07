"""Builds a chronological event timeline for a single execution."""

import threading
from typing import Any, Dict, List, Optional

from backend.observability.models import TimelineEvent


class EventTimeline:
    """Maintains an ordered list of ``TimelineEvent`` objects for one execution."""

    def __init__(self, execution_id: str) -> None:
        self._lock = threading.Lock()
        self._execution_id = execution_id
        self._events: List[TimelineEvent] = []

    def append_event(
        self,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimelineEvent:
        """Appends a new event to the timeline.

        Args:
            event_type: Category label (e.g. ``"workflow.started"``).
            description: Human-readable description of what happened.
            metadata: Optional supplemental key-value data.

        Returns:
            The appended ``TimelineEvent`` instance.
        """
        event = TimelineEvent(
            execution_id=self._execution_id,
            event_type=event_type,
            description=description,
            metadata=metadata or {},
        )
        with self._lock:
            self._events.append(event)
        return event

    def get_timeline(self) -> List[TimelineEvent]:
        """Returns an ordered copy of all recorded timeline events."""
        with self._lock:
            return list(self._events)

    def render_as_text(self) -> str:
        """Renders the timeline as a human-readable text string.

        Returns:
            Multi-line string with one event per line.
        """
        with self._lock:
            lines = []
            for i, ev in enumerate(self._events):
                prefix = "↓\n" if i > 0 else ""
                lines.append(f"{prefix}[{ev.timestamp}] {ev.event_type}: {ev.description}")
            return "\n".join(lines)
