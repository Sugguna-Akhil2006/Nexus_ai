"""FastAPI controller request parameters and mapper objects for GitHub."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """General analysis request accepting repository URLs, user names, or orgs."""
    repository_url: Optional[str] = Field(None, description="Remote GitHub repository URL or local folder path")
    username: Optional[str] = Field(None, description="Target GitHub Username")
    organization: Optional[str] = Field(None, description="Target GitHub Organization name")
    workspace_id: str = Field(..., description="Active platform workspace ID")
    user_id: str = Field("admin", description="Requesting User ID")
    branch: str = Field("main", description="Target branch context")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional overrides dictionary options")


class RepositoryRequest(BaseModel):
    """Repository-specific analysis request."""
    repository_url: str = Field(..., description="Target repository URL or local folder path")
    workspace_id: str = Field(..., description="Active workspace ID")
    user_id: str = Field("admin", description="Requesting User ID")
    branch: str = Field("main", description="Target branch context")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional overrides dictionary options")


class UserRequest(BaseModel):
    """User profile specific analysis request."""
    username: str = Field(..., description="Target GitHub username to inspect")
    workspace_id: str = Field(..., description="Active workspace ID")
    user_id: str = Field("admin", description="Requesting User ID")
    options: Optional[Dict[str, Any]] = Field(None, description="Optional overrides dictionary options")


class JobStatusResponse(BaseModel):
    """Background execution job tracking status details."""
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0 to 100
    status_msg: str
    report_id: Optional[str] = None
    result: Optional[Any] = None
