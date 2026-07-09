"""Summary generator — synthesizes executive and detailed summaries from multiple module outputs."""

from __future__ import annotations

from typing import List

from backend.intelligence.composition.models import (
    AggregatedConfidence,
    ConflictRecord,
    FindingSummary,
)
from backend.intelligence.contracts.response_models import IntelligenceResponse


class SummaryGenerator:
    """Builds executive summaries and detailed finding lists from composed output.

    All inputs come from already-executed module responses; no new analysis
    is performed here.
    """

    @staticmethod
    def generate_executive_summary(
        responses: List[IntelligenceResponse],
        aggregated_confidence: AggregatedConfidence,
        conflicts: List[ConflictRecord],
        request_id: str,
    ) -> str:
        """Generates a concise executive summary paragraph.

        Args:
            responses:             All participating module responses.
            aggregated_confidence: Pre-computed aggregated confidence.
            conflicts:             Detected conflicts (may be empty).
            request_id:            Originating request identifier.

        Returns:
            Multi-sentence executive summary as a plain-text string.
        """
        module_list = ", ".join(r.module for r in responses)
        n_modules = len(responses)
        overall_conf = aggregated_confidence.overall
        n_conflicts = len(conflicts)
        high_conflicts = [
            c for c in conflicts
            if c.severity.value in ("high", "critical")
        ]

        summary_parts: List[str] = [
            f"This report was composed from {n_modules} intelligence module(s): {module_list}. "
            f"The overall confidence score is {overall_conf:.0%}.",
        ]

        # Module-level individual summaries
        for resp in responses:
            if resp.summary:
                summary_parts.append(
                    f"[{resp.module.upper()}] {resp.summary.strip()}"
                )

        if n_conflicts == 0:
            summary_parts.append("No conflicting evidence was detected across modules.")
        elif high_conflicts:
            fields = ", ".join({c.field for c in high_conflicts})
            summary_parts.append(
                f"{len(high_conflicts)} high-severity conflict(s) were detected on field(s): "
                f"{fields}. Please review the Conflicts section."
            )
        else:
            summary_parts.append(
                f"{n_conflicts} low/medium conflict(s) were noted and resolved by confidence."
            )

        return " ".join(summary_parts)

    @staticmethod
    def extract_findings(
        responses: List[IntelligenceResponse],
    ) -> List[FindingSummary]:
        """Extracts discrete findings from each module's structured output.

        Each top-level key in ``structured_output`` that is a non-empty
        dict or list is treated as a distinct finding category.

        Args:
            responses: Module responses to extract from.

        Returns:
            Ordered list of ``FindingSummary`` objects.
        """
        findings: List[FindingSummary] = []
        seen_titles: set[str] = set()

        for resp in responses:
            for category, payload in resp.structured_output.items():
                if not payload:
                    continue
                title = f"{resp.module.capitalize()} — {category.replace('_', ' ').title()}"

                # Skip duplicate titles (same finding surfaced by two modules)
                if title in seen_titles:
                    continue
                seen_titles.add(title)

                description = (
                    payload if isinstance(payload, str)
                    else str(payload)[:300]
                )

                findings.append(FindingSummary(
                    source_modules=[resp.module],
                    category=category,
                    title=title,
                    description=description,
                    confidence=resp.confidence,
                    supporting_evidence=[
                        c.identifier for c in resp.citations[:3]
                    ],
                ))

        return findings
