"""Unit tests for Unified Knowledge Fabric module."""

from __future__ import annotations

import concurrent.futures
import unittest

from backend.knowledge_fabric.models import CanonicalEntity, EntityRelationship
from backend.knowledge_fabric.fabric_manager import FabricManager


class TestKnowledgeFabric(unittest.TestCase):
    """Test suite covering entity linking merges, lineage logs, and snapshots."""

    def setUp(self) -> None:
        self.fabric = FabricManager()
        self.fabric.clear()

    def test_entity_resolution_merges(self) -> None:
        """Verifies duplicate variants resolve to a single canonical entity."""
        # 1. Ingest 'FastAPI'
        ent1 = self.fabric.ingest_new_fact("FastAPI", "framework", "resume", "doc-1")
        self.assertEqual(ent1.name, "FastAPI")

        # 2. Ingest 'fastapi' variant
        ent2 = self.fabric.ingest_new_fact("fastapi", "framework", "github", "repo-1")
        
        # Should resolve to same canonical entity ID
        self.assertEqual(ent1.entity_id, ent2.entity_id)

    def test_knowledge_lineage_logging(self) -> None:
        """Verifies fact sources and confidence logs get recorded."""
        self.fabric.ingest_new_fact("Python", "language", "resume", "doc-123", confidence=0.95)
        
        lineages = self.fabric.tracker.get_lineage("ent-python")
        self.assertEqual(len(lineages), 1)
        self.assertEqual(lineages[0].source_module, "resume")
        self.assertEqual(lineages[0].confidence, 0.95)

    def test_graph_relationship_neighborhood(self) -> None:
        """Verifies resolving connected links neighborhood graph traversals."""
        # Ingest python and fastapi linking them
        self.fabric.ingest_new_fact("Python", "language", "resume", "doc-1")
        self.fabric.ingest_new_fact("FastAPI", "framework", "github", "repo-1", relationships_tags=["Python"])

        # Check neighborhood relationships
        rels = self.fabric.query_engine.get_neighborhood("ent-fastapi")
        self.assertEqual(len(rels), 1)
        self.assertEqual(rels[0].target_id, "ent-python")

    def test_snapshot_diffs_history(self) -> None:
        """Verifies exporting state snapshots and calculating difference changes."""
        # Ingest python -> create snapshot A
        self.fabric.ingest_new_fact("Python", "language", "resume", "doc-1")
        snap_a = self.fabric.create_state_snapshot()

        # Ingest sqlite -> create snapshot B
        self.fabric.ingest_new_fact("SQLite", "framework", "github", "repo-1")
        snap_b = self.fabric.create_state_snapshot()

        # Compare diffs
        diff = self.fabric.snapshot_mgr.diff_snapshots(snap_a.snapshot_id, snap_b.snapshot_id)
        self.assertEqual(diff["added_entities_count"], 1)
        self.assertEqual(diff["added_ids"][0], "ent-sqlite")

    def test_concurrent_fact_ingestions(self) -> None:
        """Ensures thread-safety during concurrent fact ingests."""
        def run_ingest(index: int) -> None:
            self.fabric.ingest_new_fact(f"Skill-{index}", "skill", "resume", f"doc-{index}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_ingest, i) for i in range(25)]
            concurrent.futures.wait(futures)

        entities = self.fabric.get_resolved_entities()
        self.assertEqual(len(entities), 25)
