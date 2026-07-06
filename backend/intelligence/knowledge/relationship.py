"""Represents a directed link/edge in the semantic Knowledge Graph."""

from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from backend.intelligence.knowledge.models import RelationshipType


class Relationship(BaseModel):
    """Semantic edge connecting a source node to a target node."""
    relationship_id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    evidence_sources: List[str] = Field(default_factory=list)
    supporting_documents: List[str] = Field(default_factory=list)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
