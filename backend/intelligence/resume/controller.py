"""FastAPI controller request parameters and mapper objects."""

from typing import List, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Payload response on upload completion."""
    status: str
    document_id: str
    filename: str


class AnalyzeRequest(BaseModel):
    """Resume analysis request schema."""
    document_id: str
    workspace_id: str
    user_id: str = "admin"


class MatchRequest(BaseModel):
    """Resume Job Description match request schema."""
    document_id: str
    workspace_id: str
    user_id: str = "admin"
    jd: Optional[str] = None
    job_description: Optional[str] = None
