"""Tracks manual correction overrides entered by users, prompting recalibrations."""

from datetime import datetime
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.learning.models import CorrectionEntry
from backend.intelligence.learning.experience_store import ExperienceStore


class CorrectionTracker:
    """Saves user-entered correction values on output elements."""

    def __init__(self, store: ExperienceStore) -> None:
        self.store = store
        self.event_bus = EventBus()

    def submit_correction(self, entry: CorrectionEntry) -> None:
        """Saves correction block log."""
        self.store.save_correction(entry)
        
        # Trigger confidence adjustments for the target source
        calib = self.store.get_calibration(entry.source_module)
        calib.correction_count += 1
        calib.last_updated = datetime.utcnow().isoformat()
        
        # Recalculate reliability score
        total = calib.success_count + calib.correction_count
        calib.reliability_score = max(0.2, min(1.0, 1.0 - (float(calib.correction_count) / float(max(1, total)))))
        self.store.save_calibration(calib)

        # Publish updated event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CorrectionTracker",
            payload={
                "event": "learning.confidence.updated",
                "source_key": entry.source_module,
                "reliability_score": calib.reliability_score,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
