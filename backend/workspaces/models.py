"""Pydantic data models representing workspaces, collaborative projects, artifacts, and task boards."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkspaceRole(str, Enum):
    """Permissions scopes associated with workspace roles."""

    OWNER = "owner"
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class TaskState(str, Enum):
    """Operational state of a task in the workspace board."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Project(BaseModel):
    """A long-running collaborative project workspace containing tasks and artifacts."""

    project_id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category: str = "general"
    archived: bool = False
    created_at: str


class Artifact(BaseModel):
    """A saved workspace asset (e.g. engineering report, diagram, codebase link)."""

    artifact_id: str
    project_id: str
    name: str
    artifact_type: str  # "report" | "document" | "code" | "diagram" | "export"
    content: str
    created_at: str


class ProjectTask(BaseModel):
    """An individual ticket step tracked on the task board."""

    task_id: str
    project_id: str
    title: str
    status: TaskState = TaskState.PENDING
    assignee: Optional[str] = None  # user_id or agent_id
    created_at: str


class Comment(BaseModel):
    """Discussion posts linked to a collaborative project."""

    comment_id: str
    project_id: str
    user_id: str
    content: str
    created_at: str


class ActivityRecord(BaseModel):
    """Operational event record logged in the activity feed."""

    activity_id: str
    project_id: str
    event_type: str  # "execution" | "action" | "comment" | "artifact"
    user_id: str
    description: str
    created_at: str
