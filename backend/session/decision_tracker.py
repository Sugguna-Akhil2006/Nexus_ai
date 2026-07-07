"""Decision tracker querying and filtering design/architecture decisions."""

from typing import List
from backend.session.models import Decision, DecisionType
from backend.session.project_context import ProjectContext


class DecisionTracker:
    """Helper to query, filter, and audit recorded decisions."""

    def __init__(self, project_context: ProjectContext) -> None:
        self.project_context = project_context

    def get_all_decisions(self) -> List[Decision]:
        """Returns all decisions."""
        snapshot = self.project_context.get_snapshot()
        return snapshot.architecture_decisions + snapshot.implementation_decisions

    def get_decisions_by_type(self, decision_type: DecisionType) -> List[Decision]:
        """Returns decisions filtered by type."""
        snapshot = self.project_context.get_snapshot()
        if decision_type == DecisionType.ARCHITECTURE:
            return snapshot.architecture_decisions
        return snapshot.implementation_decisions

    def search_decisions(self, query: str) -> List[Decision]:
        """Simple text search on decision titles and descriptions."""
        query_lower = query.lower()
        results = []
        for dec in self.get_all_decisions():
            if query_lower in dec.title.lower() or query_lower in dec.description.lower():
                results.append(dec)
        return results
