"""Deduplicates and merges Knowledge Graph nodes and edges."""

import re
from datetime import datetime
from typing import Dict, List, Set, Optional
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.confidence import ConfidenceEngine


class GraphMerger:
    """Detects duplicates and merges entities and relationships in the Knowledge Graph."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalizes names by lowercasing and stripping non-alphanumeric chars."""
        return re.sub(r"[^a-z0-9]", "", name.lower())

    def should_merge_nodes(self, node1: EntityNode, node2: EntityNode) -> bool:
        """Determines if two nodes represent the exact same semantic concept."""
        if node1.label != node2.label:
            return False
        return self.normalize_name(node1.name) == self.normalize_name(node2.name)

    def merge_nodes(self, node1: EntityNode, node2: EntityNode) -> EntityNode:
        """Combines two duplicate nodes into a single consolidated node."""
        # Pick the shorter or better-formatted name
        name = node1.name if len(node1.name) <= len(node2.name) else node2.name
        if not name:
            name = node1.name or node2.name

        # Merge properties
        properties = {}
        properties.update(node2.properties)
        properties.update(node1.properties)  # node1 takes precedence

        # Aggregate confidence
        confidence = ConfidenceEngine.aggregate_confidence(node1.confidence, node2.confidence)

        # Union source attributions
        evidence_sources = list(set(node1.evidence_sources + node2.evidence_sources))
        supporting_documents = list(set(node1.supporting_documents + node2.supporting_documents))

        # Capture latest timestamp
        t1 = datetime.fromisoformat(node1.last_updated)
        t2 = datetime.fromisoformat(node2.last_updated)
        last_updated = node1.last_updated if t1 >= t2 else node2.last_updated

        return EntityNode(
            node_id=node1.node_id,  # Keep the first node ID
            label=node1.label,
            name=name,
            properties=properties,
            confidence=confidence,
            evidence_sources=evidence_sources,
            supporting_documents=supporting_documents,
            last_updated=last_updated
        )

    def merge_relationships(self, rel1: Relationship, rel2: Relationship) -> Relationship:
        """Combines two duplicate relationships into a single edge."""
        properties = {}
        properties.update(rel2.properties)
        properties.update(rel1.properties)

        confidence = ConfidenceEngine.aggregate_confidence(rel1.confidence, rel2.confidence)

        evidence_sources = list(set(rel1.evidence_sources + rel2.evidence_sources))
        supporting_documents = list(set(rel1.supporting_documents + rel2.supporting_documents))

        t1 = datetime.fromisoformat(rel1.last_updated)
        t2 = datetime.fromisoformat(rel2.last_updated)
        last_updated = rel1.last_updated if t1 >= t2 else rel2.last_updated

        return Relationship(
            relationship_id=rel1.relationship_id,
            source_id=rel1.source_id,
            target_id=rel1.target_id,
            relationship_type=rel1.relationship_type,
            properties=properties,
            confidence=confidence,
            evidence_sources=evidence_sources,
            supporting_documents=supporting_documents,
            last_updated=last_updated
        )
