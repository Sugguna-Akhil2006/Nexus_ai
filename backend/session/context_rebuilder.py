"""Context rebuilder reconstructing session workspace, goals, decisions, and knowledge."""

from typing import List, Optional
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.project_context import ProjectContext
from backend.session.models import Decision, DecisionType
from backend.knowledge_fabric.fabric_manager import FabricManager
from backend.knowledge_fabric.models import CanonicalEntity
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class ContextRebuilder:
    """Rebuilds session workspace, goals, and knowledge context from past models/checkpoint or history."""

    def __init__(
        self,
        workspace_memory: WorkspaceMemory,
        project_context: ProjectContext,
        fabric_manager: Optional[FabricManager] = None
    ) -> None:
        self.workspace_memory = workspace_memory
        self.project_context = project_context
        self.fabric_manager = fabric_manager or FabricManager()
        self._event_bus = EventBus()

    def rebuild_context(
        self,
        active_project: str,
        goals: List[str],
        decisions: List[Decision],
        pending_tasks: List[str],
        recent_files: Optional[List[str]] = None,
        knowledge_query: Optional[str] = None
    ) -> List[CanonicalEntity]:
        """Reconstructs workspace states and retrieves relevant entities from the Knowledge Fabric."""
        # 1. Rebuild active workspace
        self.workspace_memory.update_project(active_project)
        if recent_files:
            for f in recent_files:
                self.workspace_memory.add_recent_file(f)
        for task in pending_tasks:
            self.workspace_memory.add_pending_task(task)

        # 2. Rebuild goals & decisions
        for goal in goals:
            self.project_context.add_goal(goal)
        for dec in decisions:
            self.project_context.record_decision(
                title=dec.title,
                description=dec.description,
                decision_type=dec.decision_type
            )

        # 3. Retrieve relevant knowledge from fabric
        relevant_entities: List[CanonicalEntity] = []
        if knowledge_query:
            relevant_entities = self.fabric_manager.search_entities(knowledge_query)

        # 4. Publish context.rebuilt event
        event = Event(
            event_type=EventType.CONTEXT_REBUILT,
            priority=EventPriority.NORMAL,
            payload={
                "project": active_project,
                "rebuilt_goals_count": len(goals),
                "rebuilt_decisions_count": len(decisions),
                "rebuilt_tasks_count": len(pending_tasks),
                "retrieved_knowledge_count": len(relevant_entities)
            }
        )
        self._event_bus.publish(event)

        return relevant_entities
