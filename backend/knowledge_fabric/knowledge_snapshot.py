"""Snapshot Manager handling exporting knowledge states and comparison diffs."""

from __future__ import annotations

from datetime import datetime
import threading
from typing import Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.knowledge_fabric.models import CanonicalEntity, EntityRelationship, KnowledgeSnapshotData


class SnapshotManager:
    """Creates versioned snapshots of the knowledge fabric entities and links."""

    def __init__(self) -> None:
        self._snapshots: Dict[str, KnowledgeSnapshotData] = {}
        self._event_bus = EventBus()
        self._lock = threading.Lock()

    def create_snapshot(self, entities: List[CanonicalEntity], relationships: List[EntityRelationship]) -> KnowledgeSnapshotData:
        """Saves current state list variables into a snapshot profile."""
        snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
        snap = KnowledgeSnapshotData(
            snapshot_id=snapshot_id,
            timestamp=datetime.utcnow(),
            entities=list(entities),
            relationships=list(relationships)
        )

        with self._lock:
            self._snapshots[snapshot_id] = snap

        # Emit event
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="SnapshotManager",
            payload={"event": "snapshot.created", "snapshot_id": snapshot_id}
        ))

        return snap

    def get_snapshot(self, snapshot_id: str) -> Optional[KnowledgeSnapshotData]:
        with self._lock:
            return self._snapshots.get(snapshot_id)

    def diff_snapshots(self, snap_a_id: str, snap_b_id: str) -> Dict[str, Any]:
        """Calculates addition/deletion changes lists between two snapshots."""
        snap_a = self.get_snapshot(snap_a_id)
        snap_b = self.get_snapshot(snap_b_id)

        if not snap_a or not snap_b:
            raise ValueError("Invalid snapshot identifier parameters.")

        entities_a = {e.entity_id for e in snap_a.entities}
        entities_b = {e.entity_id for e in snap_b.entities}

        added = entities_b - entities_a
        removed = entities_a - entities_b

        return {
            "added_entities_count": len(added),
            "removed_entities_count": len(removed),
            "added_ids": list(added),
            "removed_ids": list(removed)
        }
