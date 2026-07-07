"""Exposes reusable platform service interfaces for Research workflows."""

from typing import List, Optional
from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.research.models import ResearchAnalysisReport
from backend.intelligence.research.research_workflow import ResearchWorkflow


class ResearchService:
    """Entry service interface for research literature comparisons and graph building."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.workflow = ResearchWorkflow(db_path)

    def analyze_papers(
        self,
        workspace_id: str,
        document_ids: List[str],
        profile: Optional[KnowledgeProfile] = None
    ) -> ResearchAnalysisReport:
        """Triggers the full multi-paper analysis, comparison, and semantic reasoning pipeline."""
        return self.workflow.run_analysis(workspace_id, document_ids, profile)
