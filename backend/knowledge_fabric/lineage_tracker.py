"""Lineage Tracker logging origin details and sources of ingested facts."""

from __future__ import annotations

import sqlite3
import threading
from typing import List

from backend.api.sqlite_mock import DBStorage
from backend.knowledge_fabric.models import KnowledgeLineage


class LineageTracker:
    """Tracks origin provenance and confidence of facts stored in fabric databases."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_lineage (
                entity_id TEXT NOT NULL,
                source_module TEXT NOT NULL,
                source_ref TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_lineage(self, lineage: KnowledgeLineage) -> None:
        """Saves a lineage event to the tracker table."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO knowledge_lineage (entity_id, source_module, source_ref, confidence, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    lineage.entity_id,
                    lineage.source_module,
                    lineage.source_ref,
                    lineage.confidence,
                    lineage.created_at.isoformat()
                ))
                conn.commit()
            finally:
                conn.close()

    def get_lineage(self, entity_id: str) -> List[KnowledgeLineage]:
        """Lists source lines mapped to the entity."""
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM knowledge_lineage WHERE entity_id = ?", (entity_id,)).fetchall()
            from datetime import datetime
            return [
                KnowledgeLineage(
                    entity_id=r["entity_id"],
                    source_module=r["source_module"],
                    source_ref=r["source_ref"],
                    confidence=r["confidence"],
                    created_at=datetime.fromisoformat(r["created_at"])
                ) for r in rows
            ]
        finally:
            conn.close()

    def clear(self) -> None:
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM knowledge_lineage")
                conn.commit()
            finally:
                conn.close()
