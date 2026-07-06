"""Manages user rating ingestion and EventBus notification dispatches."""

from datetime import datetime
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.learning.models import FeedbackEntry
from backend.intelligence.learning.experience_store import ExperienceStore


class FeedbackManager:
    """Stores user evaluations, ratings, and fires EventBus signals."""

    def __init__(self, store: ExperienceStore) -> None:
        self.store = store
        self.event_bus = EventBus()

    def submit_feedback(self, entry: FeedbackEntry) -> None:
        """Stores feedback log and publishes event notification."""
        self.store.save_feedback(entry)
        
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="FeedbackManager",
            payload={
                "event": "learning.feedback.received",
                "feedback_id": entry.feedback_id,
                "workspace_id": entry.workspace_id,
                "target_type": entry.target_type,
                "feedback_type": entry.feedback_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
