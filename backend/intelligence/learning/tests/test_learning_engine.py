"""Unit and integration tests validating feedback collection and confidence optimization."""

import time
import threading
import unittest
from backend.intelligence.learning.models import FeedbackEntry, FeedbackType, CorrectionEntry
from backend.intelligence.learning.learning_engine import AdaptiveLearningEngine


class TestLearningEngine(unittest.TestCase):
    """Integration test suite verifying user feedback loops, calibrations, and settings recommendations."""

    def setUp(self) -> None:
        self.engine = AdaptiveLearningEngine()
        self.ws_id = "ws-learn-test"

    def test_feedback_ingestion(self) -> None:
        """Verifies collecting thumbs up feedback and saving to store."""
        entry = FeedbackEntry(
            feedback_id="fb-1",
            workspace_id=self.ws_id,
            target_type="reasoning",
            target_id="rep-1",
            feedback_type=FeedbackType.THUMBS_UP,
            rating=1.0,
            comments="Very accurate summary!"
        )
        self.engine.submit_feedback(entry)

        feedbacks = self.engine.store.list_feedback()
        self.assertEqual(len(feedbacks), 1)
        self.assertEqual(feedbacks[0].feedback_id, "fb-1")
        self.assertEqual(feedbacks[0].feedback_type, FeedbackType.THUMBS_UP)

    def test_correction_tracking_and_confidence_calibration(self) -> None:
        """Verifies manual corrections update starting reliability scores and penalize confidence."""
        # Baseline check (default is 1.0 reliability)
        self.assertEqual(self.engine.get_calibrated_confidence("Resume", 0.9), 0.9)

        # Log manual correction
        corr = CorrectionEntry(
            correction_id="corr-1",
            workspace_id=self.ws_id,
            source_module="Resume",
            field_name="years_experience",
            original_value="2",
            corrected_value="5"
        )
        self.engine.submit_correction(corr)

        # Calibration has 1 correction and 0 success
        # reliability_score = 1.0 - (1 / 1) = 0.0 (clamped to min_val = 0.2)
        # So calibrated confidence for base score 0.9 = 0.9 * 0.2 = 0.18
        self.assertAlmostEqual(self.engine.get_calibrated_confidence("Resume", 0.9), 0.18, places=2)

        # Log successes to recover score
        for _ in range(3):
            self.engine.record_success("Resume")

        # Now success = 3, correction = 1, total = 4
        # reliability_score = 1.0 - (1 / 4) = 0.75
        # calibrated = 0.9 * 0.75 = 0.675 -> rounded to 0.68
        self.assertAlmostEqual(self.engine.get_calibrated_confidence("Resume", 0.9), 0.68, places=2)

    def test_pattern_detection_and_recommendation_generation(self) -> None:
        """Verifies query history patterns suggest specific template workflows."""
        history = [
            "What is the latency of FastAPI backend?",
            "FastAPI performance benchmarks list",
            "Show me FastAPI optimization settings"
        ]

        patterns = self.engine.analyze_workspace_patterns(self.ws_id, history)
        self.assertTrue(any("fastapi" in p for p in patterns))

        recs = self.engine.get_recommendations(self.ws_id, history)
        self.assertTrue(any("API Benchmark Comparison" in r for r in recs))

    def test_large_history_performance(self) -> None:
        """Validates index metrics processing speed under extensive history."""
        history = [f"General query keyword query {i}" for i in range(100)]
        
        start = time.perf_counter()
        recs = self.engine.get_recommendations(self.ws_id, history)
        duration = time.perf_counter() - start

        self.assertLess(duration, 0.5)
        self.assertGreater(len(recs), 0)

    def test_concurrent_updates(self) -> None:
        """Validates thread-safe updates to registry keys."""
        exceptions = []

        def worker_success():
            try:
                for _ in range(50):
                    self.engine.record_success("GitHub")
            except Exception as e:
                exceptions.append(str(e))

        threads = [threading.Thread(target=worker_success) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Concurrency errors occurred: {exceptions}")
        calib = self.engine.store.get_calibration("GitHub")
        # 5 threads * 50 = 250 successes
        self.assertEqual(calib.success_count, 250)
