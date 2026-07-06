"""Selects appropriate modules to execute based on capabilities and inputs."""

from typing import List


class ModuleSelector:
    """Filters candidate intents according to input files availability."""

    def select_modules(
        self,
        intents: List[str],
        document_ids: List[str]
    ) -> List[str]:
        """Resolves target executable modules based on user intents and document IDs.

        Guards:
        - If "Document" or "Research" is requested but no document_ids are provided, it retains
          them only if they can query general databases, otherwise filters them out or issues warning.
        """
        selected = []
        for intent in intents:
            if intent in ("Document", "Research") and not document_ids:
                # If no documents are passed, fall back to "Resume" or "GitHub" profile queries instead
                continue
            selected.append(intent)

        # Fallback safeguard
        if not selected:
            selected.append("Resume")

        return selected
