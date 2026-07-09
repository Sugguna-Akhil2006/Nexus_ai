"""Recommendation engine suggesting templates based on workspace traits and files."""

from __future__ import annotations

from typing import List

from backend.workflow_library.models import WorkflowTemplate
from backend.workflow_library.workflow_catalog import WorkflowCatalog


class RecommendationEngine:
    """Analyzes workspace traits and suggests relevant templates from the library."""

    @staticmethod
    def suggest_templates(
        workspace_category: str,
        uploaded_files: List[str],
    ) -> List[WorkflowTemplate]:
        """Filters catalog templates matching categories and file tags.

        Args:
            workspace_category: Category tag.
            uploaded_files: List of file names.

        Returns:
            List of suggested templates.
        """
        all_templates = WorkflowCatalog.get_builtin_templates()
        suggestions = []

        category_clean = workspace_category.lower()

        for t in all_templates:
            # Suggest based on category keywords
            if "resume" in category_clean or any("resume" in f.lower() for f in uploaded_files):
                if t.template_id == "tpl-resume-review":
                    suggestions.append(t)
            elif "code" in category_clean or any("git" in f.lower() for f in uploaded_files):
                if t.template_id == "tpl-github-review":
                    suggestions.append(t)
            elif "doc" in category_clean or any("pdf" in f.lower() for f in uploaded_files):
                if t.template_id == "tpl-doc-summary":
                    suggestions.append(t)

        # Fallback default recommendations if list is empty
        if not suggestions:
            suggestions = all_templates[:2]

        return suggestions
DefinitionPath = "recommendation_engine.py"
