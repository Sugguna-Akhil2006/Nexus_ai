"""Comprehensive tests for the Intelligence Composition Layer.

Covers:
- Multi-module composition
- Conflicting evidence handling
- Missing / failed module behaviour
- Large (10-module) response composition
- Streaming / progressive composition simulation
- Confidence aggregation strategies
- Citation and artifact deduplication
- Executive summary generation
- Compare API
"""

from __future__ import annotations

import threading
import unittest
from typing import Any, Dict, List, Optional

from backend.intelligence.composition.artifact_collector import ArtifactCollector
from backend.intelligence.composition.citation_manager import CitationManager
from backend.intelligence.composition.composition_engine import CompositionEngine
from backend.intelligence.composition.confidence_aggregator import ConfidenceAggregator
from backend.intelligence.composition.conflict_detector import ConflictDetector
from backend.intelligence.composition.evidence_merger import EvidenceMerger
from backend.intelligence.composition.models import (
    CompositionStatus,
    ConfidenceStrategy,
    ConflictSeverity,
)
from backend.intelligence.composition.response_synthesizer import ResponseSynthesizer
from backend.intelligence.composition.summary_generator import SummaryGenerator
from backend.intelligence.contracts.response_models import (
    Artifact,
    Citation,
    ExecutionMetrics,
    IntelligenceResponse,
    Recommendation,
    ResponseStatus,
)
from backend.runtime.event import EventBus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reset_bus() -> None:
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {
            "published_count": 0,
            "dispatched_count": 0,
            "failed_count": 0,
            "by_type": {},
        }


def _make_response(
    module: str,
    confidence: float = 0.85,
    status: ResponseStatus = ResponseStatus.COMPLETED,
    summary: str = "",
    structured_output: Optional[Dict[str, Any]] = None,
    citations: Optional[List[Citation]] = None,
    artifacts: Optional[List[Artifact]] = None,
    recommendations: Optional[List[Recommendation]] = None,
    tokens_out: int = 500,
) -> IntelligenceResponse:
    return IntelligenceResponse(
        execution_id=f"exec-{module}",
        request_id="req-test",
        module=module,
        status=status,
        confidence=confidence,
        summary=summary or f"{module.capitalize()} analysis complete.",
        structured_output=structured_output or {f"{module}_score": confidence * 100},
        citations=citations or [],
        artifacts=artifacts or [],
        recommendations=recommendations or [],
        execution_metrics=ExecutionMetrics(
            total_duration_ms=1000.0,
            tokens_in=400,
            tokens_out=tokens_out,
            estimated_cost_usd=0.01,
        ),
    )


# ===========================================================================
# Multi-module composition tests
# ===========================================================================

class TestMultiModuleComposition(unittest.TestCase):
    """Validates composition of 3+ module responses."""

    def setUp(self) -> None:
        _reset_bus()
        self.engine = CompositionEngine()

    def test_three_module_composition(self) -> None:
        """Three successful module responses must produce COMPLETED status."""
        responses = [
            _make_response("resume", confidence=0.90),
            _make_response("github", confidence=0.80),
            _make_response("document", confidence=0.85),
        ]
        result = self.engine.compose("req-multi", responses)
        self.assertEqual(result.status, CompositionStatus.COMPLETED)
        self.assertEqual(len(result.participating_modules), 3)
        self.assertIn("resume", result.participating_modules)
        self.assertIn("github", result.participating_modules)
        self.assertGreater(result.aggregated_confidence.overall, 0.0)

    def test_executive_summary_mentions_all_modules(self) -> None:
        """Executive summary must reference all participating modules."""
        responses = [
            _make_response("resume"),
            _make_response("career"),
            _make_response("knowledge"),
        ]
        result = self.engine.compose("req-sum", responses)
        for mod in ("resume", "career", "knowledge"):
            self.assertIn(mod, result.executive_summary.lower())

    def test_structured_output_keyed_by_module(self) -> None:
        """Each module's structured output must appear under its own key."""
        responses = [
            _make_response("resume", structured_output={"skills": ["Python"]}),
            _make_response("github", structured_output={"repos": 42}),
        ]
        result = self.engine.compose("req-struct", responses)
        self.assertIn("resume", result.structured_output)
        self.assertIn("github", result.structured_output)
        self.assertEqual(result.structured_output["resume"]["skills"], ["Python"])
        self.assertEqual(result.structured_output["github"]["repos"], 42)

    def test_total_metrics_aggregated(self) -> None:
        """Total duration, tokens, and cost must sum across modules."""
        responses = [_make_response(f"mod{i}") for i in range(4)]
        result = self.engine.compose("req-metrics", responses)
        self.assertAlmostEqual(result.total_duration_ms, 4 * 1000.0)
        self.assertAlmostEqual(result.total_tokens_in, 4 * 400)
        self.assertAlmostEqual(result.estimated_cost_usd, round(4 * 0.01, 6))

    def test_composition_stored_in_history(self) -> None:
        """Composed results must be retrievable by composition_id."""
        responses = [_make_response("resume")]
        result = self.engine.compose("req-hist", responses)
        retrieved = self.engine.get_composed(result.composition_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.composition_id, result.composition_id)


# ===========================================================================
# Conflicting evidence tests
# ===========================================================================

class TestConflictingEvidence(unittest.TestCase):
    """Validates conflict detection, severity, and resolution."""

    def setUp(self) -> None:
        _reset_bus()

    def test_conflict_detected_on_shared_key(self) -> None:
        """Two modules reporting different values for the same key must produce a conflict."""
        a = _make_response("resume", structured_output={"experience_years": 5})
        b = _make_response("github", structured_output={"experience_years": 8})
        conflicts = ConflictDetector.detect([a, b])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].field, "experience_years")
        self.assertEqual(conflicts[0].module_a, "resume")
        self.assertEqual(conflicts[0].module_b, "github")

    def test_no_conflict_on_same_values(self) -> None:
        """Identical values must produce no conflicts."""
        a = _make_response("resume", structured_output={"level": "senior"})
        b = _make_response("github", structured_output={"level": "senior"})
        conflicts = ConflictDetector.detect([a, b])
        self.assertEqual(len(conflicts), 0)

    def test_conflict_severity_classification(self) -> None:
        """Large confidence delta must produce HIGH/CRITICAL severity."""
        # Big confidence gap: 0.95 vs 0.60
        a = _make_response("resume", confidence=0.95, structured_output={"x": 1})
        b = _make_response("github", confidence=0.60, structured_output={"x": 2})
        conflicts = ConflictDetector.detect([a, b])
        self.assertIn(conflicts[0].severity, (ConflictSeverity.HIGH, ConflictSeverity.CRITICAL))

    def test_auto_resolve_by_confidence(self) -> None:
        """auto_resolve=True must mark conflicts as resolved."""
        a = _make_response("resume", confidence=0.9, structured_output={"score": 10})
        b = _make_response("github", confidence=0.6, structured_output={"score": 5})
        engine = CompositionEngine(auto_resolve_conflicts=True)
        result = engine.compose("req-resolve", [a, b])
        for conflict in result.conflicts:
            self.assertTrue(conflict.resolved)

    def test_composition_contains_conflict_explanation(self) -> None:
        """Composed response must surface conflict explanation text."""
        a = _make_response("resume", structured_output={"years": 3})
        b = _make_response("github", structured_output={"years": 7})
        engine = CompositionEngine()
        result = engine.compose("req-exp", [a, b])
        self.assertEqual(len(result.conflicts), 1)
        self.assertIn("years", result.conflicts[0].explanation)


# ===========================================================================
# Missing / failed module tests
# ===========================================================================

class TestMissingModule(unittest.TestCase):
    """Validates graceful handling of partial or failed module responses."""

    def setUp(self) -> None:
        _reset_bus()
        self.engine = CompositionEngine()

    def test_empty_responses_returns_failed(self) -> None:
        """Composing with no responses must return FAILED status."""
        result = self.engine.compose("req-empty", [])
        self.assertEqual(result.status, CompositionStatus.FAILED)

    def test_partial_status_when_some_failed(self) -> None:
        """Mix of completed and failed responses must produce PARTIAL status."""
        good = _make_response("resume", status=ResponseStatus.COMPLETED)
        bad = _make_response("github", status=ResponseStatus.FAILED)
        result = self.engine.compose("req-partial", [good, bad])
        self.assertEqual(result.status, CompositionStatus.PARTIAL)

    def test_single_failed_module_summary_still_generated(self) -> None:
        """Even all-failed compositions must return an executive summary."""
        failed = _make_response("resume", status=ResponseStatus.FAILED)
        result = self.engine.compose("req-allfail", [failed])
        self.assertIsNotNone(result.executive_summary)


# ===========================================================================
# Large response tests
# ===========================================================================

class TestLargeResponse(unittest.TestCase):
    """Validates composition at scale (10 modules, 50 citations, 20 artifacts)."""

    def setUp(self) -> None:
        _reset_bus()

    def test_ten_module_composition(self) -> None:
        """Composing 10 modules must complete with correct counts."""
        modules = [
            "resume", "github", "document", "career", "professional",
            "knowledge", "research", "learning", "collaboration", "reasoning",
        ]
        responses = [_make_response(m, confidence=0.70 + i * 0.02) for i, m in enumerate(modules)]
        engine = CompositionEngine()
        result = engine.compose("req-large", responses)
        self.assertEqual(len(result.participating_modules), 10)
        self.assertEqual(result.status, CompositionStatus.COMPLETED)

    def test_citation_deduplication_at_scale(self) -> None:
        """50 citations from 5 modules where each pair shares citations must deduplicate."""
        shared_cit = Citation(source_type="document", identifier="doc-shared", title="Shared")
        responses = []
        for i in range(5):
            unique_cit = Citation(
                source_type="document", identifier=f"doc-{i}", title=f"Doc {i}"
            )
            responses.append(_make_response(
                f"mod{i}",
                citations=[shared_cit, unique_cit],
            ))

        merged = EvidenceMerger.merge_citations(responses)
        identifiers = [c.identifier for c in merged]
        # doc-shared must appear exactly once
        self.assertEqual(identifiers.count("doc-shared"), 1)
        # 5 unique docs + 1 shared = 6 total
        self.assertEqual(len(merged), 6)

    def test_artifact_deduplication_at_scale(self) -> None:
        """Artifacts with same (type, name) from multiple modules must appear once."""
        shared_art = Artifact(artifact_type="report", name="final_report", content="text")
        responses = []
        for i in range(4):
            responses.append(_make_response(
                f"mod{i}", confidence=0.5 + i * 0.1,
                artifacts=[
                    shared_art,
                    Artifact(artifact_type="json_export", name=f"export_{i}", content={}),
                ],
            ))
        collected = ArtifactCollector.collect(responses)
        report_arts = [a for a in collected if a.name == "final_report"]
        self.assertEqual(len(report_arts), 1)
        self.assertEqual(len(collected), 5)  # 1 shared + 4 unique


# ===========================================================================
# Streaming / progressive composition tests
# ===========================================================================

class TestStreamingComposition(unittest.TestCase):
    """Simulates progressive composition as modules complete asynchronously."""

    def setUp(self) -> None:
        _reset_bus()

    def test_merge_two_compositions(self) -> None:
        """Merging a later composition into a base one must include all modules."""
        engine = CompositionEngine()

        batch1 = [_make_response("resume"), _make_response("github")]
        base = engine.compose("req-stream", batch1)

        batch2 = [_make_response("document"), _make_response("career")]
        additional = engine.compose("req-stream", batch2)

        merged = engine.merge(base, additional)
        self.assertEqual(len(merged.participating_modules), 4)

    def test_compare_two_compositions(self) -> None:
        """compare() must return a dict with correct delta keys."""
        engine = CompositionEngine()
        c1 = engine.compose("req-cmp-1", [_make_response("resume", confidence=0.80)])
        c2 = engine.compose("req-cmp-2", [_make_response("resume", confidence=0.90)])

        report = engine.compare(c1, c2)
        self.assertIn("confidence", report)
        self.assertIn("delta", report["confidence"])
        self.assertGreater(report["confidence"]["delta"], 0)


# ===========================================================================
# Confidence aggregation tests
# ===========================================================================

class TestConfidenceAggregation(unittest.TestCase):
    """Validates each aggregation strategy."""

    def _responses(self) -> List[IntelligenceResponse]:
        return [
            _make_response("resume", confidence=0.90, tokens_out=600),
            _make_response("github", confidence=0.70, tokens_out=200),
            _make_response("document", confidence=0.80, tokens_out=400),
        ]

    def test_average_strategy(self) -> None:
        agg = ConfidenceAggregator.aggregate(self._responses(), ConfidenceStrategy.AVERAGE)
        self.assertAlmostEqual(agg.overall, (0.90 + 0.70 + 0.80) / 3, places=3)

    def test_min_strategy(self) -> None:
        agg = ConfidenceAggregator.aggregate(self._responses(), ConfidenceStrategy.MIN)
        self.assertAlmostEqual(agg.overall, 0.70, places=3)

    def test_max_strategy(self) -> None:
        agg = ConfidenceAggregator.aggregate(self._responses(), ConfidenceStrategy.MAX)
        self.assertAlmostEqual(agg.overall, 0.90, places=3)

    def test_weighted_average_is_reasonable(self) -> None:
        agg = ConfidenceAggregator.aggregate(
            self._responses(), ConfidenceStrategy.WEIGHTED_AVERAGE
        )
        # Should be between min and max
        self.assertGreater(agg.overall, 0.70)
        self.assertLess(agg.overall, 0.90)

    def test_manual_weights_applied(self) -> None:
        agg = ConfidenceAggregator.aggregate(
            self._responses(),
            ConfidenceStrategy.WEIGHTED_AVERAGE,
            manual_weights={"resume": 0.8, "github": 0.1, "document": 0.1},
        )
        # Heavy weight on resume (0.90) should push overall close to 0.90
        self.assertGreater(agg.overall, 0.85)

    def test_empty_responses_returns_zero(self) -> None:
        agg = ConfidenceAggregator.aggregate([], ConfidenceStrategy.AVERAGE)
        self.assertEqual(agg.overall, 0.0)


# ===========================================================================
# Citation manager tests
# ===========================================================================

class TestCitationManager(unittest.TestCase):
    """Validates CitationManager index, filter, rank, and render."""

    def setUp(self) -> None:
        self.mgr = CitationManager()
        self.mgr.add_many([
            Citation(source_type="document", identifier="d1", title="Doc 1", relevance_score=0.9),
            Citation(source_type="url", identifier="u1", title="URL 1", relevance_score=0.6),
            Citation(source_type="document", identifier="d2", title="Doc 2", relevance_score=0.75),
        ])

    def test_total_count(self) -> None:
        self.assertEqual(len(self.mgr), 3)

    def test_filter_by_source_type(self) -> None:
        docs = self.mgr.filter_by_source_type("document")
        self.assertEqual(len(docs), 2)
        self.assertEqual(docs[0].identifier, "d1")  # higher relevance first

    def test_top_n(self) -> None:
        top2 = self.mgr.top_n(2)
        self.assertEqual(len(top2), 2)
        self.assertEqual(top2[0].identifier, "d1")

    def test_markdown_rendering(self) -> None:
        md = self.mgr.to_markdown()
        self.assertIn("## References", md)
        self.assertIn("Doc 1", md)
