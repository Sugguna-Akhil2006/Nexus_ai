"""Shared execution context carrying state and memory between pipeline stages."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IntelligenceContext(BaseModel):
    """Context holding user workspace details, document IDs, memory, and intermediate stage outputs."""
    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    conversation_id: Optional[str] = None
    memory: Dict[str, Any] = Field(default_factory=dict)
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True
