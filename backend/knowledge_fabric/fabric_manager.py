"""Fabric Manager facade coordinating entity links, relationships, and snapshots."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.knowledge_fabric.models import CanonicalEntity, EntityRelationship, KnowledgeSnapshotData
from backend.knowledge_fabric.entity_linker import EntityLinker
from backend.knowledge_fabric.relationship_resolver import RelationshipResolver
from backend.knowledge_fabric.lineage_tracker import LineageTracker
from backend.knowledge_fabric.provenance_manager import ProvenanceManager
from backend.knowledge_fabric.semantic_index import SemanticIndex
from backend.knowledge_fabric.knowledge_ingestor import KnowledgeIngestor
from backend.knowledge_fabric.fabric_query_engine import FabricQueryEngine
from backend.knowledge_fabric.knowledge_snapshot import SnapshotManager
from backend.knowledge_fabric.fabric_registry import FabricRegistry


class FabricManager:
    """Central administrative interface coordinating the Unified Knowledge Fabric."""

    def __init__(self) -> None:
        self.linker = EntityLinker()
        self.resolver = RelationshipResolver()
        self.tracker = LineageTracker()
        self.provenance = ProvenanceManager()
        self.index = SemanticIndex()
        self.ingestor = KnowledgeIngestor(self.linker)
        self.query_engine = FabricQueryEngine(self.index)
        self.snapshot_mgr = SnapshotManager()
        self.registry = FabricRegistry()

    def ingest_new_fact(
        self,
        name: str,
        category: str,
        source_module: str,
        source_ref: str,
        confidence: float = 1.0,
        relationships_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CanonicalEntity:
        """Ingests fact and dynamically resolves and logs its relationships."""
        entity = self.ingestor.ingest_fact(
            name=name,
            category=category,
            source_module=source_module,
            source_ref=source_ref,
            confidence=confidence,
            metadata=metadata
        )

        if relationships_tags:
            rels = self.resolver.resolve_relationships(entity.entity_id, relationships_tags)
            for r in rels:
                self.query_engine.add_relationship(r)

        return entity

    def get_resolved_entities(self) -> List[CanonicalEntity]:
        return self.ingestor.list_entities()

    def search_entities(self, query: str) -> List[CanonicalEntity]:
        all_ent = self.ingestor.list_entities()
        return self.index.search_similar_entities(all_ent, query)

    def create_state_snapshot(self) -> KnowledgeSnapshotData:
        all_ent = self.ingestor.list_entities()
        all_rels = self.query_engine.list_relationships()
        return self.snapshot_mgr.create_snapshot(all_ent, all_rels)

    def clear(self) -> None:
        self.ingestor.clear()
        self.query_engine.clear()
        self.tracker.clear()
