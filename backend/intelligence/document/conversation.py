"""Data models representing request inputs and response payloads for conversational AI."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.intelligence.document.document_model import Citation


class ChatRequest(BaseModel):
    """Payload to continue a document chat conversation turn."""
    workspace_id: str
    query: str
    conversation_id: Optional[str] = None
    document_ids: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Payload to perform isolated vector, keyword, or hybrid searches."""
    workspace_id: str
    query: str
    document_ids: Optional[List[str]] = None
    search_mode: str = "HYBRID"  # SEMANTIC, KEYWORD, HYBRID
    limit: int = 5
    options: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    """Indexed segment list response payload."""
    results: List[Dict[str, Any]] = Field(default_factory=list)


class DocumentConversationResponse(BaseModel):
    """Interactive response containing citations, confidence, and suggested follow-up questions."""
    answer: str
    summary: str
    evidence: str
    citations: List[Citation] = Field(default_factory=list)
    confidence: float
    related_documents: List[str] = Field(default_factory=list)
    suggested_follow_up_questions: List[str] = Field(default_factory=list)
    conversation_id: str
