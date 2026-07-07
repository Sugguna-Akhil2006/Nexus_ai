"""Relationship Resolver building directed relationship links between entities."""

from __future__ import annotations

import uuid
from typing import List

from backend.knowledge_fabric.models import EntityRelationship


class RelationshipResolver:
    """Links resolved entities together forming semantic connections."""

    def resolve_relationships(self, source_id: str, tags: List[str]) -> List[EntityRelationship]:
        """Resolves associations list between source entity and tags."""
        relationships = []
        for tag in tags:
            target_id = f"ent-{tag.strip().lower()}"
            relationships.append(EntityRelationship(
                relationship_id=f"rel-{uuid.uuid4().hex[:8]}",
                source_id=source_id,
                target_id=target_id,
                relation_type="skilled_in"
            ))
        return relationships
