"""FastAPI APIRouter routing project workspaces CRUDs, comments, task boards, and searches."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.workspaces.models import TaskState
from backend.workspaces.workspace_manager import WorkspaceManager

router = APIRouter(prefix="/workspaces", tags=["AI Workspaces"])

# Singleton manager
_manager = WorkspaceManager()


class CreateProjectPayload(BaseModel):
    """Payload to create a project."""

    workspace_id: str
    user_id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    category: str = "general"


class AddTaskPayload(BaseModel):
    """Payload to add a task ticket."""

    project_id: str
    user_id: str
    title: str
    assignee: Optional[str] = None


class AddArtifactPayload(BaseModel):
    """Payload to add an artifact."""

    project_id: str
    user_id: str
    name: str
    artifact_type: str
    content: str


class AddCommentPayload(BaseModel):
    """Payload to add a discussion post comment."""

    project_id: str
    user_id: str
    content: str


@router.post("/projects", summary="Create a new workspace project")
def create_project(payload: CreateProjectPayload) -> Any:
    """Creates a project and saves it to the SQLite relational tables."""
    proj = _manager.create_project(
        workspace_id=payload.workspace_id,
        user_id=payload.user_id,
        name=payload.name,
        description=payload.description,
        tags=payload.tags,
        category=payload.category,
    )
    return ProductResponse.ok(data=proj)


@router.get("/projects", summary="List active workspace projects")
def get_projects(workspace_id: str = Query(...)) -> ProductResponse[List[Any]]:
    """Lists all active projects defined in a workspace tenant."""
    projects = _manager.projects.list_projects(workspace_id)
    return ProductResponse.ok(data=projects)


@router.post("/tasks", summary="Add a task ticket to the project board")
def add_task(payload: AddTaskPayload) -> Any:
    """Creates a task ticket and saves it to the SQLite tasks tables."""
    task = _manager.add_task(
        project_id=payload.project_id,
        user_id=payload.user_id,
        title=payload.title,
        assignee=payload.assignee,
    )
    return ProductResponse.ok(data=task)


@router.post("/artifacts", summary="Store an asset artifact in a project")
def add_artifact(payload: AddArtifactPayload) -> Any:
    """Saves a report, diagram, or code asset artifact link to a project."""
    art = _manager.add_artifact(
        project_id=payload.project_id,
        user_id=payload.user_id,
        name=payload.name,
        artifact_type=payload.artifact_type,
        content=payload.content,
    )
    return ProductResponse.ok(data=art)


@router.post("/comments", summary="Add a comment to project discussion thread")
def add_comment(payload: AddCommentPayload) -> Any:
    """Saves a discussion post comment."""
    com = _manager.comments.add_comment(
        project_id=payload.project_id,
        user_id=payload.user_id,
        content=payload.content,
    )
    return ProductResponse.ok(data=com)


@router.get("/search", summary="Search across projects and artifacts")
def get_search(
    workspace_id: str = Query(...),
    query: str = Query(...),
) -> ProductResponse[List[Any]]:
    """Performs wildcard string search queries across projects, tasks, and artifacts."""
    hits = _manager.search_engine.search(workspace_id, query)
    return ProductResponse.ok(data=hits)
