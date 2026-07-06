"""Unit and integration tests for the Unified AI Reasoning Engine."""

import time
import threading
import unittest
from backend.intelligence.reasoning.models import ReasoningRequest, Evidence, Conflict
from backend.intelligence.reasoning.reasoning_engine import UnifiedReasoningEngine


class TestReasoningEngine(unittest.TestCase):
    """Integrates and tests the UnifiedReasoningEngine pipeline, checkers, and fusers."""

    def setUp(self) -> None:
        self.engine = UnifiedReasoningEngine()
        self.ws_id = "ws-reason-test"

    def test_single_source_reasoning(self) -> None:
        """Verifies parsing and conclusion generation over a single source file."""
        ev = Evidence(
            evidence_id="e-1",
            source="Resume",
            fact="Alice has 5 years of Python programming experience.",
            confidence=0.9
        )
        
        req = ReasoningRequest(
            workspace_id=self.ws_id,
            query="Does Alice know Python?",
            sources=[ev]
        )
        report = self.engine.execute_reasoning(req)

        self.assertEqual(len(report.collected_evidence), 1)
        self.assertEqual(report.confidence, 0.9)
        self.assertTrue(any("Alice has 5 years of Python" in c for c in report.final_conclusions))
        self.assertGreater(len(report.reasoning_trace), 0)

    def test_multi_source_and_duplicate_fusion(self) -> None:
        """Verifies correlation and duplication merges across multi-source feeds."""
        ev1 = Evidence(
            evidence_id="e-1",
            source="Resume",
            fact="Alice is proficient in building backend systems using React.",
            confidence=0.8
        )
        ev2 = Evidence(
            evidence_id="e-2",
            source="GitHub",
            fact="Alice is proficient in building backend systems using React.",  # Identical fact
            confidence=0.9
        )
        
        req = ReasoningRequest(
            workspace_id=self.ws_id,
            query="Which frontend frameworks does Alice use?",
            sources=[ev1, ev2]
        )
        report = self.engine.execute_reasoning(req)

        # Knowledge fusion should merge these duplicates into 1 evidence
        self.assertEqual(len(report.collected_evidence), 1)
        # Combined source name
        self.assertIn("Resume", report.collected_evidence[0].source)
        self.assertIn("GitHub", report.collected_evidence[0].source)
        # Max confidence score used
        self.assertEqual(report.collected_evidence[0].confidence, 0.9)

    def test_conflict_detection_contradictions(self) -> None:
        """Verifies clashing assertions prompt contradictions and confidence penalties."""
        ev1 = Evidence(
            evidence_id="e-1",
            source="SourceA",
            fact="Benchmark tests prove FastAPI increases response performance.",
            confidence=1.0
        )
            # Opposite polarity assertion
        ev2 = Evidence(
            evidence_id="e-2",
            source="SourceB",
            fact="Benchmark tests prove FastAPI decreases response performance.",
            confidence=0.8
        )

        req = ReasoningRequest(
            workspace_id=self.ws_id,
            query="How does FastAPI affect performance?",
            sources=[ev1, ev2]
        )
        report = self.engine.execute_reasoning(req)

        # Contradiction should be detected
        conflicts = [c for c in report.detected_conflicts if c.category == "Contradictory Sources"]
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].severity, "High")

        # Confidence should be penalized (-0.15)
        # Avg base confidence = (1.0 + 0.8) / 2 = 0.9. Final confidence = 0.9 - 0.15 = 0.75
        self.assertAlmostEqual(report.confidence, 0.75, places=2)

    def test_missing_evidence_and_low_confidence(self) -> None:
        """Validates keyword gaps and low confidence scoring limits."""
        ev = Evidence(
            evidence_id="e-1",
            source="SourceA",
            fact="General system details.",
            confidence=0.4  # Low confidence
        )

        req = ReasoningRequest(
            workspace_id=self.ws_id,
            query="Does the system support Kubernetes?",
            sources=[ev]
        )
        report = self.engine.execute_reasoning(req)

        # Anomaly categories
        categories = {c.category for c in report.detected_conflicts}
        self.assertIn("Missing Evidence", categories)
        self.assertIn("Low Confidence", categories)

    def test_large_reasoning_graph(self) -> None:
        """Validates processing speed on a substantial array of items."""
        sources = []
        for i in range(50):
            sources.append(Evidence(
                evidence_id=f"e-{i}",
                source=f"Source{i}",
                fact=f"General fact indexing technical keyword Python and reference code {i}.",
                confidence=0.8
            ))

        req = ReasoningRequest(
            workspace_id=self.ws_id,
            query="Search keyword Python reference",
            sources=sources
        )
        
        start = time.perf_counter()
        report = self.engine.execute_reasoning(req)
        duration = time.perf_counter() - start

        self.assertLess(duration, 1.0, "Reasoning execution took too long.")
        self.assertGreater(len(report.collected_evidence), 0)

    def test_concurrent_requests(self) -> None:
        """Validates that concurrent threads executing reasoning do not share state."""
        exceptions = []

        def worker_run(idx: int):
            try:
                ev = Evidence(
                    evidence_id=f"e-{idx}",
                    source=f"Source{idx}",
                    fact=f"Specific thread isolated test fact {idx}",
                    confidence=0.9
                )
                req = ReasoningRequest(
                    workspace_id=self.ws_id,
                    query=f"isolated test {idx}",
                    sources=[ev]
                )
                report = self.engine.execute_reasoning(req)
                if len(report.collected_evidence) != 1 or f"isolated test fact {idx}" not in report.collected_evidence[0].fact:
                    exceptions.append(f"Thread {idx} got wrong evidence count/fact")
            except Exception as e:
                exceptions.append(str(e))

        threads = [threading.Thread(target=worker_run, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Concurrency exceptions occurred: {exceptions}")
