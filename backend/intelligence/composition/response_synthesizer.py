"""Response synthesizer — merges all sub-outputs into one ``ComposedResponse``."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.intelligence.composition.artifact_collector import ArtifactCollector
from backend.intelligence.composition.citation_manager import CitationManager
from backend.intelligence.composition.confidence_aggregator import ConfidenceAggregator
from backend.intelligence.composition.conflict_detector import ConflictDetector
from backend.intelligence.composition.evidence_merger import EvidenceMerger
from backend.intelligence.composition.models import (
    AggregatedConfidence,
    ComposedResponse,
    CompositionStatus,
    ConfidenceStrategy,
    ModuleContribution,
)
from backend.intelligence.composition.summary_generator import SummaryGenerator
from backend.intelligence.contracts.response_models import (
    IntelligenceResponse,
    Recommendation,
    ResponseStatus,
)


class ResponseSynthesizer:
    """Orchestrates all composition sub-modules into a single ``ComposedResponse``.

    Does **not** invoke intelligence modules — it consumes their already-
    completed ``IntelligenceResponse`` objects and produces a unified report.
    """

    def __init__(
        self,
        strategy: ConfidenceStrategy = ConfidenceStrategy.WEIGHTED_AVERAGE,
        manual_weights: Optional[Dict[str, float]] = None,
        auto_resolve_conflicts: bool = True,
    ) -> None:
        self._strategy = strategy
        self._manual_weights = manual_weights
        self._auto_resolve = auto_resolve_conflicts

    def synthesize(
        self,
        request_id: str,
        responses: List[IntelligenceResponse],
    ) -> ComposedResponse:
        """Builds the composed response from a list of module responses.

        Args:
            request_id: Originating request identifier (echoed into the output).
            responses:  Non-empty list of ``IntelligenceResponse`` objects.

        Returns:
            ``ComposedResponse`` with all sections populated.
        """
        if not responses:
            return ComposedResponse(
                request_id=request_id,
                status=CompositionStatus.FAILED,
                executive_summary="No module responses provided for composition.",
            )

        # ── 1. Confidence aggregation ─────────────────────────────────
        agg_confidence: AggregatedConfidence = ConfidenceAggregator.aggregate(
            responses, self._strategy, self._manual_weights
        )

        # ── 2. Conflict detection (+ optional resolution) ─────────────
        conflicts = ConflictDetector.detect(responses)
        if self._auto_resolve:
            conflicts = [
                ConflictDetector.resolve_by_confidence(c, responses)
                for c in conflicts
            ]

        # ── 3. Citation merging ───────────────────────────────────────
        merged_citations = EvidenceMerger.merge_citations(responses)
        merged_citations = EvidenceMerger.remove_duplicate_snippets(merged_citations)
        citation_mgr = CitationManager()
        citation_mgr.add_many(merged_citations)

        # ── 4. Artifact collection ────────────────────────────────────
        artifacts = ArtifactCollector.collect(responses)

        # ── 5. Recommendation deduplication (by title) ────────────────
        recommendations = self._merge_recommendations(responses)

        # ── 6. Structured output merge (module_name → sub-dict) ───────
        structured_output: Dict = {
            r.module: r.structured_output
            for r in responses
            if r.structured_output
        }

        # ── 7. Summary generation ─────────────────────────────────────
        executive_summary = SummaryGenerator.generate_executive_summary(
            responses, agg_confidence, conflicts, request_id
        )
        findings = SummaryGenerator.extract_findings(responses)

        # ── 8. Module contributions ───────────────────────────────────
        contributions = [
            ModuleContribution(
                module=r.module,
                execution_id=r.execution_id,
                status=r.status,
                confidence=r.confidence,
                summary=r.summary,
                structured_output=r.structured_output,
                citation_ids=[c.citation_id for c in r.citations],
                artifact_ids=[a.artifact_id for a in r.artifacts],
                recommendation_ids=[rec.recommendation_id for rec in r.recommendations],
            )
            for r in responses
        ]

        # ── 9. Aggregate metrics ──────────────────────────────────────
        total_dur = sum(r.execution_metrics.total_duration_ms for r in responses)
        total_in = sum(r.execution_metrics.tokens_in for r in responses)
        total_out = sum(r.execution_metrics.tokens_out for r in responses)
        total_cost = sum(r.execution_metrics.estimated_cost_usd for r in responses)

        # ── 10. Overall status ────────────────────────────────────────
        all_ok = all(r.status == ResponseStatus.COMPLETED for r in responses)
        any_ok = any(r.status == ResponseStatus.COMPLETED for r in responses)
        status = (
            CompositionStatus.COMPLETED if all_ok
            else CompositionStatus.PARTIAL if any_ok
            else CompositionStatus.FAILED
        )

        return ComposedResponse(
            request_id=request_id,
            status=status,
            participating_modules=[r.module for r in responses],
            module_contributions=contributions,
            executive_summary=executive_summary,
            detailed_findings=findings,
            structured_output=structured_output,
            citations=citation_mgr.all_citations(),
            artifacts=artifacts,
            recommendations=recommendations,
            aggregated_confidence=agg_confidence,
            conflicts=conflicts,
            total_duration_ms=total_dur,
            total_tokens_in=total_in,
            total_tokens_out=total_out,
            estimated_cost_usd=round(total_cost, 6),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_recommendations(
        responses: List[IntelligenceResponse],
    ) -> List[Recommendation]:
        """Deduplicates recommendations by title across all modules."""
        seen_titles: set[str] = set()
        merged: List[Recommendation] = []

        # Process higher-confidence modules first
        sorted_responses = sorted(responses, key=lambda r: r.confidence, reverse=True)
        for resp in sorted_responses:
            for rec in resp.recommendations:
                title_key = rec.title.strip().lower()
                if title_key not in seen_titles:
                    seen_titles.add(title_key)
                    merged.append(rec)

        return merged
