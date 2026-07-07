"""Knowledge Ingestor resolving fact metadata and inserting entities in fabric databases."""

from __future__ import annotations

from datetime import datetime
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType
from backend.knowledge_fabric.models import CanonicalEntity, KnowledgeLineage
from backend.knowledge_fabric.entity_linker import EntityLinker


class KnowledgeIngestor:
    """Ingests raw facts, linking duplicate tokens to canonical entities."""

    def __init__(self, linker: Optional[EntityLinker] = None) -> None:
        self._db = DBStorage()
        self.linker = linker or EntityLinker()
        self._event_bus = EventBus()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_entities (
                entity_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def ingest_fact(
        self,
        name: str,
        category: str,
        source_module: str,
        source_ref: str,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CanonicalEntity:
        """Ingests fact, resolving canonical entities and logging lineage records."""
        import json
        canonical_name = self.linker.resolve_canonical_name(name)
        ent_id = self.linker.generate_entity_id(canonical_name)

        entity = CanonicalEntity(
            entity_id=ent_id,
            name=canonical_name,
            category=category,
            metadata=metadata or {}
        )

        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO knowledge_entities (entity_id, name, category, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(entity_id) DO UPDATE SET
                    name=excluded.name,
                    category=excluded.category,
                    metadata=excluded.metadata
                """, (
                    ent_id,
                    canonical_name,
                    category,
                    json.dumps(entity.metadata)
                ))
                conn.commit()
            finally:
                conn.close()

        # Log lineage
        from backend.knowledge_fabric.lineage_tracker import LineageTracker
        tracker = LineageTracker()
        tracker.log_lineage(KnowledgeLineage(
            entity_id=ent_id,
            source_module=source_module,
            source_ref=source_ref,
            confidence=confidence,
            created_at=datetime.utcnow()
        ))

        # Emit events
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeIngestor",
            payload={"event": "knowledge.ingested", "entity_id": ent_id, "name": canonical_name}
        ))
        
        if canonical_name != name:
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="KnowledgeIngestor",
                payload={"event": "entity.linked", "raw_name": name, "canonical_name": canonical_name}
            ))

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="KnowledgeIngestor",
            payload={"event": "fabric.updated"}
        ))

        return entity

    def list_entities(self) -> List[CanonicalEntity]:
        conn = self._db._get_connection()
        try:
            import json
            rows = conn.execute("SELECT * FROM knowledge_entities").fetchall()
            return [
                CanonicalEntity(
                    entity_id=r["entity_id"],
                    name=r["name"],
                    category=r["category"],
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                ) for r in rows
            ]
        finally:
            conn.close()

    def clear(self) -> None:
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM knowledge_entities")
                conn.commit()
            finally:
                conn.close()
