"""Thread-safe SQLite storage manager for Knowledge Graph nodes and edges."""

import sqlite3
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType


class GraphStorage:
    """Manages transactional query executions on SQLite for nodes and relationships."""

    _lock = threading.RLock()

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=60.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes knowledge graph node and relationship tables if not present."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Nodes Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph_nodes (
                node_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                label TEXT NOT NULL,
                name TEXT NOT NULL,
                properties TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_sources TEXT NOT NULL,
                supporting_documents TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (workspace_id, node_id)
            )
            """)

            # Relationships Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_graph_relationships (
                relationship_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                properties TEXT NOT NULL,
                confidence REAL NOT NULL,
                evidence_sources TEXT NOT NULL,
                supporting_documents TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (workspace_id, relationship_id)
            )
            """)
            
            conn.commit()
            conn.close()

    def upsert_node(self, workspace_id: str, node: EntityNode) -> None:
        """Stores or modifies a node entry."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_graph_nodes (
                    node_id, workspace_id, label, name, properties, 
                    confidence, evidence_sources, supporting_documents, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node.node_id,
                    workspace_id,
                    node.label.value,
                    node.name,
                    json.dumps(node.properties),
                    node.confidence,
                    json.dumps(node.evidence_sources),
                    json.dumps(node.supporting_documents),
                    node.last_updated
                )
            )
            conn.commit()
            conn.close()

    def get_node(self, workspace_id: str, node_id: str) -> Optional[EntityNode]:
        """Retrieves a node by identifier."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM knowledge_graph_nodes WHERE workspace_id = ? AND node_id = ?",
                (workspace_id, node_id)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            
            return EntityNode(
                node_id=row["node_id"],
                label=EntityType(row["label"]),
                name=row["name"],
                properties=json.loads(row["properties"]),
                confidence=row["confidence"],
                evidence_sources=json.loads(row["evidence_sources"]),
                supporting_documents=json.loads(row["supporting_documents"]),
                last_updated=row["last_updated"]
            )

    def delete_node(self, workspace_id: str, node_id: str) -> None:
        """Deletes a node and all of its associated relationships."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM knowledge_graph_nodes WHERE workspace_id = ? AND node_id = ?",
                (workspace_id, node_id)
            )
            cursor.execute(
                "DELETE FROM knowledge_graph_relationships WHERE workspace_id = ? AND (source_id = ? OR target_id = ?)",
                (workspace_id, node_id, node_id)
            )
            conn.commit()
            conn.close()

    def list_nodes(self, workspace_id: str) -> List[EntityNode]:
        """Lists all nodes in a workspace."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_graph_nodes WHERE workspace_id = ?", (workspace_id,))
            rows = cursor.fetchall()
            conn.close()
            
            nodes = []
            for row in rows:
                nodes.append(EntityNode(
                    node_id=row["node_id"],
                    label=EntityType(row["label"]),
                    name=row["name"],
                    properties=json.loads(row["properties"]),
                    confidence=row["confidence"],
                    evidence_sources=json.loads(row["evidence_sources"]),
                    supporting_documents=json.loads(row["supporting_documents"]),
                    last_updated=row["last_updated"]
                ))
            return nodes

    def upsert_relationship(self, workspace_id: str, rel: Relationship) -> None:
        """Stores or modifies a relationship entry."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_graph_relationships (
                    relationship_id, workspace_id, source_id, target_id, relationship_type,
                    properties, confidence, evidence_sources, supporting_documents, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rel.relationship_id,
                    workspace_id,
                    rel.source_id,
                    rel.target_id,
                    rel.relationship_type.value,
                    json.dumps(rel.properties),
                    rel.confidence,
                    json.dumps(rel.evidence_sources),
                    json.dumps(rel.supporting_documents),
                    rel.last_updated
                )
            )
            conn.commit()
            conn.close()

    def get_relationship(self, workspace_id: str, rel_id: str) -> Optional[Relationship]:
        """Retrieves a relationship."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM knowledge_graph_relationships WHERE workspace_id = ? AND relationship_id = ?",
                (workspace_id, rel_id)
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            
            return Relationship(
                relationship_id=row["relationship_id"],
                source_id=row["source_id"],
                target_id=row["target_id"],
                relationship_type=RelationshipType(row["relationship_type"]),
                properties=json.loads(row["properties"]),
                confidence=row["confidence"],
                evidence_sources=json.loads(row["evidence_sources"]),
                supporting_documents=json.loads(row["supporting_documents"]),
                last_updated=row["last_updated"]
            )

    def delete_relationship(self, workspace_id: str, rel_id: str) -> None:
        """Removes a relationship."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM knowledge_graph_relationships WHERE workspace_id = ? AND relationship_id = ?",
                (workspace_id, rel_id)
            )
            conn.commit()
            conn.close()

    def list_relationships(self, workspace_id: str) -> List[Relationship]:
        """Lists all relationships in a workspace."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_graph_relationships WHERE workspace_id = ?", (workspace_id,))
            rows = cursor.fetchall()
            conn.close()
            
            relationships = []
            for row in rows:
                relationships.append(Relationship(
                    relationship_id=row["relationship_id"],
                    source_id=row["source_id"],
                    target_id=row["target_id"],
                    relationship_type=RelationshipType(row["relationship_type"]),
                    properties=json.loads(row["properties"]),
                    confidence=row["confidence"],
                    evidence_sources=json.loads(row["evidence_sources"]),
                    supporting_documents=json.loads(row["supporting_documents"]),
                    last_updated=row["last_updated"]
                ))
            return relationships

    def clear_graph(self, workspace_id: str) -> None:
        """Removes all nodes and relationships of a workspace."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_graph_nodes WHERE workspace_id = ?", (workspace_id,))
            cursor.execute("DELETE FROM knowledge_graph_relationships WHERE workspace_id = ?", (workspace_id,))
            conn.commit()
            conn.close()
