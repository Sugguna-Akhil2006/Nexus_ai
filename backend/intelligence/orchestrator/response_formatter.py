"""Formats unified response summaries and metadata traces."""

import uuid
from typing import List, Dict, Any
from backend.intelligence.orchestrator.models import UnifiedIntelligenceResponse


class ResponseFormatter:
    """Assembles and formats the final UnifiedIntelligenceResponse payload."""

    def format_response(
        self,
        modules_executed: List[str],
        timeline: List[Dict[str, Any]],
        reasoning_report: Any
    ) -> UnifiedIntelligenceResponse:
        """Packages reasoning engine output and execution metrics into a unified structure."""
        # Synthesize final natural response
        conclusions_str = "\n".join([f"- {c}" for c in reasoning_report.final_conclusions])
        final_response = (
            f"Nexus AI Orchestrator resolved query using context from {', '.join(modules_executed)} modules.\n\n"
            f"### Consolidated Conclusions:\n{conclusions_str}\n\n"
            f"### Anomalies & Conflicts Checked:\n"
            f"Discrepancies flagged: {len(reasoning_report.detected_conflicts)} instances."
        )

        return UnifiedIntelligenceResponse(
            response_id=f"res-orch-{str(uuid.uuid4())[:8]}",
            modules_executed=modules_executed,
            execution_timeline=timeline,
            evidence_sources=reasoning_report.supporting_sources,
            confidence_score=reasoning_report.confidence,
            reasoning_summary=f"Fuesd {len(reasoning_report.collected_evidence)} facts. Final confidence weight: {reasoning_report.confidence}.",
            final_response=final_response
        )
