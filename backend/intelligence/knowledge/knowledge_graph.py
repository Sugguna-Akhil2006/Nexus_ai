"""Orchestrates top-level Knowledge Graph capabilities, EventBus notifications, and Unified Profile syncing."""

from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.knowledge.graph_storage import GraphStorage
from backend.intelligence.knowledge.graph_builder import GraphBuilder
from backend.intelligence.knowledge.graph_search import GraphSearcher
from backend.intelligence.knowledge.semantic_reasoner import SemanticReasoner


class KnowledgeGraphEngine:
    """Master engine orchestrator for all semantic indexing, queries, eventing, and reasoning."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.storage = GraphStorage(db_path)
        self.builder = GraphBuilder(self.storage)
        self.searcher = GraphSearcher(self.storage)
        self.reasoner = SemanticReasoner(self.storage)
        self.event_bus = EventBus()

    def add_node(self, workspace_id: str, node: EntityNode) -> str:
        """Adds or merges an entity node, publishing relevant lifecycle telemetry events."""
        existing_nodes = self.storage.list_nodes(workspace_id)
        is_new = True
        
        for ext in existing_nodes:
            if self.builder.merger.should_merge_nodes(ext, node):
                is_new = False
                break

        node_id = self.builder.add_or_merge_node(workspace_id, node)

        # Publish event telemetry
        evt_name = "knowledge.node.created" if is_new else "knowledge.graph.updated"
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": evt_name,
                "workspace_id": workspace_id,
                "node_id": node_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        return node_id

    def add_relationship(self, workspace_id: str, rel: Relationship) -> None:
        """Adds or merges a semantic edge, publishing Edge telemetry events."""
        existing_rels = self.storage.list_relationships(workspace_id)
        is_new = True

        for ext in existing_rels:
            if ext.source_id == rel.source_id and ext.target_id == rel.target_id and ext.relationship_type == rel.relationship_type:
                is_new = False
                break

        self.builder.add_or_merge_relationship(workspace_id, rel)

        evt_name = "knowledge.relationship.created" if is_new else "knowledge.graph.updated"
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": evt_name,
                "workspace_id": workspace_id,
                "relationship_id": rel.relationship_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def get_node(self, workspace_id: str, node_id: str) -> Optional[EntityNode]:
        """Retrieves a node from the database store."""
        return self.storage.get_node(workspace_id, node_id)

    def get_relationship(self, workspace_id: str, rel_id: str) -> Optional[Relationship]:
        """Retrieves a relationship from the database store."""
        return self.storage.get_relationship(workspace_id, rel_id)

    def delete_node(self, workspace_id: str, node_id: str) -> None:
        """Removes a node and its connections, emitting graph updated events."""
        self.storage.delete_node(workspace_id, node_id)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.graph.updated",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def delete_relationship(self, workspace_id: str, rel_id: str) -> None:
        """Removes a relationship, emitting graph updated events."""
        self.storage.delete_relationship(workspace_id, rel_id)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.graph.updated",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def list_nodes(self, workspace_id: str) -> List[EntityNode]:
        """Retrieves all nodes in a workspace."""
        return self.storage.list_nodes(workspace_id)

    def list_relationships(self, workspace_id: str) -> List[Relationship]:
        """Retrieves all relationships in a workspace."""
        return self.storage.list_relationships(workspace_id)

    def ingest_resume(self, workspace_id: str, resume_data: Dict[str, Any]) -> None:
        """Ingests structured Resume profile details."""
        self.builder.build_from_resume(workspace_id, resume_data)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.graph.updated",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def ingest_github(self, workspace_id: str, github_report: Dict[str, Any]) -> None:
        """Ingests structured GitHub repository metrics."""
        self.builder.build_from_github(workspace_id, github_report)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.graph.updated",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def ingest_document(self, workspace_id: str, document_report: Dict[str, Any]) -> None:
        """Ingests structured Document metadata and extracted entities."""
        self.builder.build_from_document(workspace_id, document_report)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.graph.updated",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

    def find_paths(
        self,
        workspace_id: str,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 3
    ) -> List[List[Relationship]]:
        """Finds all paths between two nodes up to max_depth."""
        return self.searcher.find_paths(workspace_id, start_node_id, end_node_id, max_depth)

    def get_neighborhood(
        self,
        workspace_id: str,
        node_id: str,
        depth: int = 1
    ) -> Tuple[List[EntityNode], List[Relationship]]:
        """Gets neighborhood subgraph around target node."""
        return self.searcher.get_neighborhood(workspace_id, node_id, depth)

    def search_similar_nodes(
        self,
        workspace_id: str,
        target_node_id: str,
        limit: int = 5
    ) -> List[Tuple[EntityNode, float]]:
        """Finds top-N similar nodes using Jaccard connection overlaps."""
        return self.searcher.search_similar_nodes(workspace_id, target_node_id, limit)

    def run_reasoning(self, workspace_id: str) -> Dict[str, Any] :
        """Executes rule-based logical inference and logs metrics reports."""
        res = self.reasoner.execute_reasoning(workspace_id)
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeGraphEngine",
            payload={
                "event": "knowledge.reasoning.completed",
                "workspace_id": workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        return res

    def sync_profile(self, workspace_id: str, profile: KnowledgeProfile) -> None:
        """Synchronizes the SQLite graph content with the Unified Knowledge Profile graph dict."""
        nodes = self.storage.list_nodes(workspace_id)
        rels = self.storage.list_relationships(workspace_id)

        # Mapping entity type labels to UKP keys
        prefix_map = {
            EntityType.PROJECT: "project:",
            EntityType.SKILL: "skill:",
            EntityType.TECHNOLOGY: "skill:",
            EntityType.PROGRAMMING_LANGUAGE: "skill:",
            EntityType.FRAMEWORK: "skill:",
            EntityType.LIBRARY: "skill:",
            EntityType.COMPANY: "company:",
            EntityType.ORGANIZATION: "company:",
            EntityType.PERSON: "person:",
            EntityType.REPOSITORY: "repo:",
            EntityType.DOCUMENT: "doc:"
        }

        node_lookup = {n.node_id: n for n in nodes}

        def get_key(node_id: str) -> str:
            n = node_lookup.get(node_id)
            if not n:
                return f"unknown:{node_id}"
            prefix = prefix_map.get(n.label, f"{n.label.value.lower()}:")
            return f"{prefix}{n.name}"

        # Consolidate edges into standard dictionary format
        graph_dict = {}
        for r in rels:
            src_key = get_key(r.source_id)
            tgt_key = get_key(r.target_id)
            graph_dict.setdefault(src_key, []).append(tgt_key)

        profile.knowledge_graph = {k: sorted(list(set(v))) for k, v in graph_dict.items()}
        profile.last_updated = datetime.utcnow().isoformat()
