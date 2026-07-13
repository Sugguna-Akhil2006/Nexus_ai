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
        core_modules = ["resume", "github", "document", "professional", "research"]
        check_modules = list(set(core_modules + [m.lower() for m in available_modules]))


        if explicit_modules:
            return explicit_modules

        # Simple semantic/keyword intent parsing fallback
        if isinstance(query, list):
            query_str = " ".join(query)
        else:
            query_str = query
        query_lower = query_str.lower()
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
            # Check if mod is matched in check_modules (either directly or as a substring)
            has_module = False
            for m in check_modules:
                if mod.lower() in m.lower():
                    has_module = True
                    break
            if has_module:
                if any(kw in query_lower for kw in keywords):
                    selected.add(mod.capitalize() if mod != "github" else "GitHub")

        # Match based on document presence
        if document_ids:
            # check if document is in registered modules
            if any("document" in m.lower() for m in check_modules):
                selected.add("Document")

        # Fallback to general modules if nothing matched
        if not selected:
            # Default to Document or Research if available, otherwise first module
            doc_mod = next((m for m in check_modules if "document" in m.lower()), None)
            if doc_mod:
                selected.add("Document")
            elif check_modules:
                first_name = check_modules[0]
                # Map to short name
                for key in mappings.keys():
                    if key.lower() in first_name.lower():
                        selected.add(key.capitalize() if key != "github" else "GitHub")
                        break
                else:
                    selected.add(first_name)

        return sorted(list(selected))

