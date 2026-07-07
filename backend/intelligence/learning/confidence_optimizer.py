"""Adjusts module reliability ratings based on historical successes and failures."""

from datetime import datetime
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.learning.experience_store import ExperienceStore


class ConfidenceOptimizer:
    """Recalculates reliability scores and applies calibrated weights."""

    def __init__(self, store: ExperienceStore) -> None:
        self.store = store
        self.event_bus = EventBus()

    def record_success(self, source_key: str) -> None:
        """Increments success count for a module and recalculates score."""
        calib = self.store.get_calibration(source_key)
        calib.success_count += 1
        calib.last_updated = datetime.utcnow().isoformat()
        
        self._recalculate(calib)

    def record_failure(self, source_key: str) -> None:
        """Increments failure/correction count for a module and recalculates score."""
        calib = self.store.get_calibration(source_key)
        calib.correction_count += 1
        calib.last_updated = datetime.utcnow().isoformat()
        
        self._recalculate(calib)

    def get_calibrated_confidence(self, source_key: str, base_confidence: float) -> float:
        """Multiplies base confidence score with dynamic historical reliability."""
        calib = self.store.get_calibration(source_key)
        calibrated = base_confidence * calib.reliability_score
        return round(max(0.1, min(1.0, calibrated)), 2)

    def _recalculate(self, calib) -> None:
        """Recalculates reliability score logic."""
        total = calib.success_count + calib.correction_count
        calib.reliability_score = max(0.2, min(1.0, 1.0 - (float(calib.correction_count) / float(max(1, total)))))
        self.store.save_calibration(calib)

        # Publish update
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ConfidenceOptimizer",
            payload={
                "event": "learning.confidence.updated",
                "source_key": calib.source_key,
                "reliability_score": calib.reliability_score,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
