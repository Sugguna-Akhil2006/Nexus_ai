"""Compiles the final unified ResearchAnalysisReport structure."""

import uuid
from typing import Dict, List, Any
from backend.intelligence.research.models import ResearchAnalysisReport, ResearchPaperMetadata


class ResearchReportBuilder:
    """Builds and constructs consolidated ResearchAnalysisReport instances."""

    def compile_report(
        self,
        summary: str,
        findings: List[str],
        evidence_matrix: List[Dict[str, Any]],
        comparison: Dict[str, Any],
        topics: List[str],
        kg_updates: Dict[str, List[str]],
        gaps: List[str],
        suggested_reading: List[str],
        citations: List[Dict[str, Any]],
        confidence_scores: Dict[str, float]
    ) -> ResearchAnalysisReport:
        """Constructs and returns the final serialized ResearchAnalysisReport."""
        return ResearchAnalysisReport(
            report_id=f"rep-res-{str(uuid.uuid4())[:8]}",
            executive_summary=summary,
            key_findings=findings,
            evidence_matrix=evidence_matrix,
            source_comparison=comparison,
            topics=topics,
            knowledge_graph_updates=kg_updates,
            research_gaps=gaps,
            suggested_reading=suggested_reading,
            citations=citations,
            confidence_scores=confidence_scores
        )
