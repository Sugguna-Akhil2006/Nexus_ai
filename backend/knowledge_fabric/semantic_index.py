"""Semantic Index performing keyword similarity checks across entities."""

from __future__ import annotations

from typing import List

from backend.knowledge_fabric.models import CanonicalEntity


class SemanticIndex:
    """Keyword search indices for canonical entities matching similarity scores."""

    def search_similar_entities(self, entities: List[CanonicalEntity], query: str) -> List[CanonicalEntity]:
        """Filters entities containing query prefix or substring."""
        q = query.lower().strip()
        matched = []
        for e in entities:
            if q in e.name.lower() or q in e.category.lower():
                matched.append(e)
        return matched
