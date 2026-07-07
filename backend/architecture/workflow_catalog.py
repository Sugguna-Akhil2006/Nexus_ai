"""Workflow catalog listing execution steps and predefined orchestration flows."""

from __future__ import annotations

from typing import Any, Dict, List


class WorkflowCatalog:
    """Structures descriptions for predefined system workflows."""

    @staticmethod
    def get_workflows() -> List[Dict[str, Any]]:
        """Returns configurations and steps for standard orchestrations.

        Returns:
            List of workflow details.
        """
        return [
            {
                "workflow_id": "resume_intelligence_flow",
                "name": "Resume Screening",
                "steps": ["ExtractText", "ParseSkills", "EvaluateATS"],
                "trigger": "Resume PDF upload",
            },
            {
                "workflow_id": "github_analysis_flow",
                "name": "Engineering Metrics Ingestion",
                "steps": ["CloneRepo", "AnalyzeLanguages", "AuditCodeQuality"],
                "trigger": "GitHub URL connection",
            },
            {
                "workflow_id": "knowledge_fabric_flow",
                "name": "RAG Document Indexing",
                "steps": ["ParseFiles", "ChunkText", "EmbedVector", "IndexReferences"],
                "trigger": "Technical documents upload",
            },
        ]
DefinitionPath = "workflow_catalog.py"
