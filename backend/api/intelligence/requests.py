"""Standard request schemas for the Intelligence API Gateway."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GatewayExecutionRequest(BaseModel):
    """Standardized API request payload for all intelligence executions."""
    workspace_id: str = Field(..., description="Target workspace ID")
    user_id: Optional[str] = Field(None, description="Requesting User ID")
    conversation_id: Optional[str] = Field(None, description="Active conversation context ID")
    document_ids: List[str] = Field(default_factory=list, description="Associated document context IDs")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata payload inputs (e.g. raw text, files)")
    capability: str = Field(..., description="Target module capability keyword (e.g. RESUME_PARSING)")
