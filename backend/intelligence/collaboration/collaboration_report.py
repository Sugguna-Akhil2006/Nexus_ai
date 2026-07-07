"""Assembles finalized summaries and timelines into the CollaborationReport Pydantic model."""

import uuid
from typing import List, Dict, Any
from backend.intelligence.collaboration.models import CollaborationReport


class CollaborationReportBuilder:
    """Assembles context metadata and facts into structured reports."""

    def build_report(
        self,
        session_id: str,
        objective: str,
        executed_agents: List[str],
        timeline: List[Dict[str, Any]],
        shared_evidence: List[Dict[str, Any]],
        reasoning_report: Any
    ) -> CollaborationReport:
        """Constructs and returns a populated CollaborationReport structure."""
        return CollaborationReport(
            report_id=f"rep-collab-{str(uuid.uuid4())[:8]}",
            session_id=session_id,
            objective=objective,
            executed_agents=executed_agents,
            shared_evidence=shared_evidence,
            resolved_conclusions=reasoning_report.final_conclusions,
            confidence_score=reasoning_report.confidence,
            timeline=timeline
        )
