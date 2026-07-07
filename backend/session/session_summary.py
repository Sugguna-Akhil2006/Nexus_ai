"""Session summary generator analyzing completed tasks, progress, next actions, and open issues."""

from typing import List
from backend.session.models import SessionSummaryModel
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.project_context import ProjectContext
from backend.session.reasoning_history import ReasoningHistory


class SessionSummary:
    """Generates human-readable and structured summaries of session achievements and status."""

    def __init__(
        self,
        workspace_memory: WorkspaceMemory,
        project_context: ProjectContext,
        reasoning_history: ReasoningHistory
    ) -> None:
        self.workspace_memory = workspace_memory
        self.project_context = project_context
        self.reasoning_history = reasoning_history

    def generate_summary(self) -> SessionSummaryModel:
        """Analyzes active state structures to formulate a session summary."""
        mem_snapshot = self.workspace_memory.get_snapshot()
        ctx_snapshot = self.project_context.get_snapshot()
        reasoning_snapshot = self.reasoning_history.get_snapshot()

        # What was completed: completed reports or tasks that were removed (we can infer from reasoning reports/recommendations)
        completed = list(reasoning_snapshot.generated_reports)
        if not completed:
            completed = ["No reports generated in this session."]

        # Current progress description
        current_progress = f"Working on project '{mem_snapshot.current_project or 'None'}' towards objective: '{mem_snapshot.current_objective or 'No active objective'}'."

        # Next recommended actions: derived from recommendations, pending tasks, or default suggestions
        next_actions = list(reasoning_snapshot.recommendations)
        if mem_snapshot.pending_tasks:
            next_actions.extend(mem_snapshot.pending_tasks[:3])
        if not next_actions:
            next_actions = ["Define high-level objectives", "Review pending project issues"]

        # Open issues: from known issues
        open_issues = list(ctx_snapshot.known_issues)
        if not open_issues:
            open_issues = ["No critical open issues recorded."]

        return SessionSummaryModel(
            completed=completed,
            current_progress=current_progress,
            next_recommended_actions=next_actions,
            open_issues=open_issues
        )
