"""Represents a node in the semantic Knowledge Graph."""

from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
from backend.intelligence.knowledge.models import EntityType


class EntityNode(BaseModel):
    """Immutable-ready node entry representing an extracted professional entity."""
    node_id: str
    label: EntityType
    name: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    evidence_sources: List[str] = Field(default_factory=list)  # names of source systems
    supporting_documents: List[str] = Field(default_factory=list)  # document IDs
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
