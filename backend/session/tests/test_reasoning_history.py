"""Tests for reasoning history tracker."""

import unittest
from backend.session.reasoning_history import ReasoningHistory


class TestReasoningHistory(unittest.TestCase):
    """Verifies that ReasoningHistory captures reasoning details correctly."""

    def test_recording(self) -> None:
        """Tests adding questions, evidence, steps, reports, and recommendations."""
        history = ReasoningHistory()
        history.record_question("What is the state of Epic 9?")
        history.record_evidence("Workspace memory is implemented")
        history.record_step("Verify test files exist", confidence=0.95)
        history.record_step("Execute test suite", confidence=1.0)
        history.record_report("Epic 9 Report")
        history.record_recommendation("Run coverage analysis")

        snapshot = history.get_snapshot()
        self.assertEqual(snapshot.questions_asked, ["What is the state of Epic 9?"])
        self.assertEqual(snapshot.evidence_used, ["Workspace memory is implemented"])
        self.assertEqual(len(snapshot.reasoning_steps), 2)
        self.assertEqual(snapshot.reasoning_steps[0].description, "Verify test files exist")
        self.assertEqual(snapshot.reasoning_steps[0].confidence, 0.95)
        self.assertEqual(snapshot.generated_reports, ["Epic 9 Report"])
        self.assertEqual(snapshot.recommendations, ["Run coverage analysis"])
        self.assertEqual(snapshot.confidence_evolution, [0.95, 1.0])
