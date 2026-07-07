"""Data schemas representing canonical entities, relationships, lineage logs, and snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CanonicalEntity:
    """A single canonical entity resolved across multiple sources."""

    entity_id: str
    name: str
    category: str  # skill, framework, organization, language
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EntityRelationship:
    """Directed relationship link between two canonical entities."""

    relationship_id: str
    source_id: str
    target_id: str
    relation_type: str  # skilled_in, belongs_to, depends_on
    confidence: float = 1.0


@dataclass
class KnowledgeLineage:
    """Source origin details, evidence, and confidence limits."""

    entity_id: str
    source_module: str  # resume, github, document, connector
    source_ref: str
    confidence: float
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class KnowledgeSnapshotData:
    """Consolidated state payload representing a full Knowledge Fabric snapshot."""

    snapshot_id: str
    timestamp: datetime
    entities: List[CanonicalEntity] = field(default_factory=list)
    relationships: List[EntityRelationship] = field(default_factory=list)
