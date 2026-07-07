"""Data models for Workspace Management & Enterprise User Experience."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WorkspaceSettings(BaseModel):
    """Configuration settings for a workspace."""
    industry: str = "Technology & SaaS"
    deployment: str = "private"  # cloud | private
    description: str = ""


class WorkspaceDetail(BaseModel):
    """Complete detail of a workspace, including flags and metadata."""
    workspace_id: str
    name: str
    owner_id: str
    status: str = "active"  # active | archived | deleted
    created_at: datetime
    updated_at: datetime
    is_pinned: bool = False
    is_favorite: bool = False
    settings: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceCreatePayload(BaseModel):
    """Request payload to create a new workspace."""
    name: str
    owner_id: str = "admin"
    settings: Optional[WorkspaceSettings] = None


class WorkspaceUpdatePayload(BaseModel):
    """Request payload to update an existing workspace."""
    name: Optional[str] = None
    status: Optional[str] = None  # active | archived | deleted
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    settings: Optional[WorkspaceSettings] = None
    metadata: Optional[Dict[str, Any]] = None


class ActivityRecord(BaseModel):
    """Log record representing an action performed in a workspace."""
    activity_id: str
    workspace_id: str
    user_id: str
    activity_type: str  # upload | analysis | export | workspace_change | report_generation
    description: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceStats(BaseModel):
    """Aggregated statistics for a workspace dashboard."""
    total_documents: int = 0
    total_analyses: int = 0
    total_repositories: int = 0
    ai_usage_count: int = 0
    storage_used_bytes: int = 0
    document_types: Dict[str, int] = Field(default_factory=dict)
    recent_activity_count: int = 0


class WorkspaceDashboardData(BaseModel):
    """Unified payload returned to render the Workspace Dashboard."""
    workspace: WorkspaceDetail
    stats: WorkspaceStats
    recent_analyses: List[Dict[str, Any]] = Field(default_factory=list)
    pinned_reports: List[Dict[str, Any]] = Field(default_factory=list)
    recent_documents: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[ActivityRecord] = Field(default_factory=list)


class SearchQueryPayload(BaseModel):
    """Unified search request payload."""
    query: str
    types: List[str] = Field(default_factory=lambda: ["document", "report", "repository", "history"])
    limit: int = 20


class SearchResultItem(BaseModel):
    """Single item matched during a unified search."""
    id: str
    name: str
    type: str  # document | report | repository | history
    snippet: str
    workspace_id: str
    score: float = 1.0
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
