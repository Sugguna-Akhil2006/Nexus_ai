"""Thread-safe in-memory cache persistency layer for learning profiles."""

import threading
from typing import Dict, List, Optional
from backend.intelligence.learning.models import FeedbackEntry, CorrectionEntry
from backend.intelligence.learning.learning_models import ConfidenceCalibration, UserPreference


class ExperienceStore:
    """Thread-safe store stashing user feedbacks, calibrations, and settings preferences."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._feedback: Dict[str, FeedbackEntry] = {}
        self._corrections: Dict[str, CorrectionEntry] = {}
        self._calibrations: Dict[str, ConfidenceCalibration] = {}
        self._preferences: Dict[str, UserPreference] = {}

    def save_feedback(self, entry: FeedbackEntry) -> None:
        """Stores a FeedbackEntry thread-safely."""
        with self._lock:
            self._feedback[entry.feedback_id] = entry

    def list_feedback(self) -> List[FeedbackEntry]:
        """Lists all captured feedback entries."""
        with self._lock:
            return list(self._feedback.values())

    def save_correction(self, entry: CorrectionEntry) -> None:
        """Stores a CorrectionEntry thread-safely."""
        with self._lock:
            self._corrections[entry.correction_id] = entry

    def list_corrections(self) -> List[CorrectionEntry]:
        """Lists all captured correction entries."""
        with self._lock:
            return list(self._corrections.values())

    def save_calibration(self, entry: ConfidenceCalibration) -> None:
        """Stores a source ConfidenceCalibration block."""
        with self._lock:
            self._calibrations[entry.source_key] = entry

    def get_calibration(self, source_key: str) -> ConfidenceCalibration:
        """Fetches calibration metrics block or initializes default if missing."""
        with self._lock:
            if source_key not in self._calibrations:
                self._calibrations[source_key] = ConfidenceCalibration(source_key=source_key)
            return self._calibrations[source_key]

    def save_preference(self, entry: UserPreference) -> None:
        """Saves a UserPreference tracking block."""
        key = f"{entry.workspace_id}:{entry.category}:{entry.value}"
        with self._lock:
            if key in self._preferences:
                self._preferences[key].frequency += entry.frequency
            else:
                self._preferences[key] = entry

    def get_preferences(self, workspace_id: str) -> List[UserPreference]:
        """Lists preference records registered for a workspace."""
        with self._lock:
            return [p for p in self._preferences.values() if p.workspace_id == workspace_id]
