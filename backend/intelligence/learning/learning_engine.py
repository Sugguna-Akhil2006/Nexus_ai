"""Unified Adaptive Learning & Feedback Engine coordinator facade."""

from typing import List, Dict, Any, Optional
from backend.intelligence.learning.models import FeedbackEntry, CorrectionEntry
from backend.intelligence.learning.experience_store import ExperienceStore
from backend.intelligence.learning.feedback_manager import FeedbackManager
from backend.intelligence.learning.correction_tracker import CorrectionTracker
from backend.intelligence.learning.confidence_optimizer import ConfidenceOptimizer
from backend.intelligence.learning.pattern_detector import PatternDetector
from backend.intelligence.learning.recommendation_engine import RecommendationEngine


class AdaptiveLearningEngine:
    """Manages adaptive calibrations, feedback ingestion, and preference updates."""

    def __init__(self) -> None:
        self.store = ExperienceStore()
        self.feedback_manager = FeedbackManager(self.store)
        self.correction_tracker = CorrectionTracker(self.store)
        self.confidence_optimizer = ConfidenceOptimizer(self.store)
        self.pattern_detector = PatternDetector(self.store)
        self.recommendation_engine = RecommendationEngine(self.store)

    def submit_feedback(self, entry: FeedbackEntry) -> None:
        """Submits thumbs up/down or ratings feedback log."""
        self.feedback_manager.submit_feedback(entry)

    def submit_correction(self, entry: CorrectionEntry) -> None:
        """Submits manual correction and updates confidence calibrations."""
        self.correction_tracker.submit_correction(entry)

    def record_success(self, source_key: str) -> None:
        """Records a successful analysis execution for confidence optimizer calibration."""
        self.confidence_optimizer.record_success(source_key)

    def record_failure(self, source_key: str) -> None:
        """Records a failed analysis execution/correction."""
        self.confidence_optimizer.record_failure(source_key)

    def get_calibrated_confidence(self, source_key: str, base_confidence: float) -> float:
        """Multiplies base confidence score with dynamic historical reliability."""
        return self.confidence_optimizer.get_calibrated_confidence(source_key, base_confidence)

    def analyze_workspace_patterns(self, workspace_id: str, query_history: List[str]) -> List[str]:
        """Runs pattern detector to isolate repeated search terms."""
        return self.pattern_detector.detect_patterns(workspace_id, query_history)

    def get_recommendations(self, workspace_id: str, query_history: List[str]) -> List[str]:
        """Detects patterns and compiles personalized suggested workflows."""
        patterns = self.analyze_workspace_patterns(workspace_id, query_history)
        return self.recommendation_engine.generate_recommendations(workspace_id, patterns)
