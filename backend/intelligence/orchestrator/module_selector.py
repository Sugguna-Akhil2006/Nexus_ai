"""Module selector matching queries or intents to registered Intelligence modules."""

from __future__ import annotations

import logging
from typing import List, Set

from backend.intelligence.core.registry import IntelligenceRegistry

logger = logging.getLogger("nexus.orchestrator.selector")


class ModuleSelector:
    """Discovers and selects registered modules based on input query terms and attachments."""

    def __init__(self) -> None:
        self._registry = IntelligenceRegistry()

    def select_modules(
        self,
        query: str,
        document_ids: List[str],
        explicit_modules: Optional[List[str]] = None,
    ) -> List[str]:
        """Identifies target modules required to satisfy the orchestration request.

        Args:
            query: User's intent query.
            document_ids: Attached document identifiers.
            explicit_modules: Optional list of modules explicitly requested.

        Returns:
            List of matching module names.
        """
        available_modules = self._registry.list_modules()
        # Fallback to known modules list if registry is empty (e.g. during startup/testing)
        check_modules = available_modules if available_modules else ["resume", "github", "document", "professional", "research"]

        if explicit_modules:
            return explicit_modules

        # Simple semantic/keyword intent parsing fallback
        query_lower = query.lower()
        selected: Set[str] = set()

        # Keyword mapping
        mappings = {
            "resume": ["resume", "cv", "candidate", "applicant", "career"],
            "github": ["github", "git", "repo", "codebase", "commit"],
            "document": ["document", "pdf", "docx", "text", "file"],
            "professional": ["professional", "portfolio", "score", "evaluate"],
            "research": ["research", "paper", "literature", "article"],
        }

        # Match query keywords
        for mod, keywords in mappings.items():
            if mod in check_modules:
                if any(kw in query_lower for kw in keywords):
                    selected.add(mod)

        # Match based on document presence
        if document_ids:
            if "document" in available_modules:
                selected.add("document")

        # Fallback to general modules if nothing matched
        if not selected:
            # Default to document or research if available, otherwise first module
            if "document" in available_modules:
                selected.add("document")
            elif available_modules:
                selected.add(available_modules[0])

        return sorted(list(selected))
