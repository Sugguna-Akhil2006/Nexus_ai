"""Query Engine traversing resolved semantic knowledge graphs."""

from __future__ import annotations

import sqlite3
import threading
from typing import Any, Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.knowledge_fabric.models import CanonicalEntity, EntityRelationship
from backend.knowledge_fabric.semantic_index import SemanticIndex


class FabricQueryEngine:
    """Traverses knowledge entity links and performs neighborhood search scans."""

    def __init__(self, semantic_index: Optional[SemanticIndex] = None) -> None:
        self._db = DBStorage()
        self.semantic_index = semantic_index or SemanticIndex()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_relationships (
                relationship_id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                relation_type TEXT NOT NULL,
                confidence REAL NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def add_relationship(self, rel: EntityRelationship) -> None:
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO knowledge_relationships (relationship_id, source_id, target_id, relation_type, confidence)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(relationship_id) DO UPDATE SET
                    source_id=excluded.source_id,
                    target_id=excluded.target_id,
                    relation_type=excluded.relation_type,
                    confidence=excluded.confidence
                """, (
                    rel.relationship_id,
                    rel.source_id,
                    rel.target_id,
                    rel.relation_type,
                    rel.confidence
                ))
                conn.commit()
            finally:
                conn.close()

    def get_neighborhood(self, entity_id: str) -> List[EntityRelationship]:
        """Resolves connected relationships directed to or from the entity."""
        conn = self._db._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM knowledge_relationships WHERE source_id = ? OR target_id = ?",
                (entity_id, entity_id)
            ).fetchall()
            return [
                EntityRelationship(
                    relationship_id=r["relationship_id"],
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    relation_type=r["relation_type"],
                    confidence=r["confidence"]
                ) for r in rows
            ]
        finally:
            conn.close()

    def list_relationships(self) -> List[EntityRelationship]:
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM knowledge_relationships").fetchall()
            return [
                EntityRelationship(
                    relationship_id=r["relationship_id"],
                    source_id=r["source_id"],
                    target_id=r["target_id"],
                    relation_type=r["relation_type"],
                    confidence=r["confidence"]
                ) for r in rows
            ]
        finally:
            conn.close()

    def clear(self) -> None:
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM knowledge_relationships")
                conn.commit()
            finally:
                conn.close()
