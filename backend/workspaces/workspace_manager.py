"""Workspace manager coordinating project managers, task boards, comments, and permissions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.workspaces.activity_feed import ActivityFeed
from backend.workspaces.artifact_manager import ArtifactManager
from backend.workspaces.comment_service import CommentService
from backend.workspaces.models import ActivityRecord, Artifact, Project, ProjectTask, TaskState
from backend.workspaces.project_manager import ProjectManager
from backend.workspaces.task_board import TaskBoard
from backend.workspaces.workspace_permissions import WorkspacePermissions
from backend.workspaces.workspace_search import WorkspaceSearch


class WorkspaceManager:
    """The central manager (facade) coordinating all project workspace functionalities."""

    _instance: Optional["WorkspaceManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "WorkspaceManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        self.projects = ProjectManager(db_path)
        self.artifacts = ArtifactManager(db_path)
        self.tasks = TaskBoard(db_path)
        self.feed = ActivityFeed(db_path)
        self.comments = CommentService(db_path)
        self.search_engine = WorkspaceSearch(db_path)
        self.permissions = WorkspacePermissions(db_path)
        self._initialized = True

    # ------------------------------------------------------------------
    # Facade Wrappers
    # ------------------------------------------------------------------

    def create_project(
        self,
        workspace_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
    ) -> Project:
        """Creates a project and logs the update in the activity feed."""
        proj = self.projects.create_project(workspace_id, name, description, tags, category)
        self.feed.log_activity(
            project_id=proj.project_id,
            event_type="action",
            user_id=user_id,
            description=f"Project '{name}' was created.",
        )
        return proj

    def add_artifact(
        self,
        project_id: str,
        user_id: str,
        name: str,
        artifact_type: str,
        content: str,
    ) -> Artifact:
        """Stores a workspace asset and logs the update in the activity feed."""
        art = self.artifacts.add_artifact(project_id, name, artifact_type, content)
        self.feed.log_activity(
            project_id=project_id,
            event_type="artifact",
            user_id=user_id,
            description=f"Artifact '{name}' ({artifact_type}) was added.",
        )
        return art

    def add_task(
        self,
        project_id: str,
        user_id: str,
        title: str,
        assignee: Optional[str] = None,
    ) -> ProjectTask:
        """Adds a task ticket to the board and logs the update in the activity feed."""
        task = self.tasks.add_task(project_id, title, assignee)
        self.feed.log_activity(
            project_id=project_id,
            event_type="action",
            user_id=user_id,
            description=f"Task ticket '{title}' was added.",
        )
        return task

    def update_task_status(
        self,
        project_id: str,
        task_id: str,
        user_id: str,
        status: TaskState,
    ) -> None:
        """Updates the state of a task and logs the update in the activity feed."""
        self.tasks.update_task_status(task_id, status)
        self.feed.log_activity(
            project_id=project_id,
            event_type="action",
            user_id=user_id,
            description=f"Task status updated to '{status.value}'.",
        )
