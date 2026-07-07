"""Unit and integration tests for the Knowledge Graph & Semantic Reasoning Engine."""

import os
import time
import uuid
import threading
import unittest
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.knowledge.knowledge_graph import KnowledgeGraphEngine
from backend.intelligence.profile.models import KnowledgeProfile


class TestKnowledgeGraph(unittest.TestCase):
    """Integrates and tests the KnowledgeGraphEngine features and rules."""

    def setUp(self) -> None:
        # Create an isolated temporary SQLite database for testing
        self.db_name = f"test_graph_{str(uuid.uuid4())[:8]}.db"
        self.engine = KnowledgeGraphEngine(db_path=self.db_name)
        self.ws_id = "ws-test"

    def tearDown(self) -> None:
        # Clean up temporary database files
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except Exception:
                pass

    def test_graph_creation(self) -> None:
        """Verifies basic creation, upserting, retrieval, and deletion of nodes/relationships."""
        node1 = EntityNode(
            node_id="person-alice",
            label=EntityType.PERSON,
            name="Alice Vance",
            properties={"title": "Tech Lead"},
            confidence=0.9,
            evidence_sources=["Test"]
        )
        node2 = EntityNode(
            node_id="proj-nexus",
            label=EntityType.PROJECT,
            name="Nexus AI",
            properties={"stage": "Beta"},
            confidence=0.8,
            evidence_sources=["Test"]
        )

        n1_id = self.engine.add_node(self.ws_id, node1)
        n2_id = self.engine.add_node(self.ws_id, node2)

        self.assertEqual(n1_id, "person-alice")
        self.assertEqual(n2_id, "proj-nexus")

        # Fetch nodes
        fetched_n1 = self.engine.get_node(self.ws_id, "person-alice")
        self.assertIsNotNone(fetched_n1)
        self.assertEqual(fetched_n1.name, "Alice Vance")

        # Create relationship
        rel = Relationship(
            relationship_id="rel-alice-nexus",
            source_id="person-alice",
            target_id="proj-nexus",
            relationship_type=RelationshipType.WORKED_ON,
            confidence=0.85,
            evidence_sources=["Test"]
        )
        self.engine.add_relationship(self.ws_id, rel)

        fetched_rel = self.engine.get_relationship(self.ws_id, "rel-alice-nexus")
        self.assertIsNotNone(fetched_rel)
        self.assertEqual(fetched_rel.relationship_type, RelationshipType.WORKED_ON)

    def test_graph_merge_and_duplicate_detection(self) -> None:
        """Verifies duplicate concepts are deduplicated and merged with aggregated confidence."""
        # Add Python as Technology
        node1 = EntityNode(
            node_id="lang-python-raw",
            label=EntityType.PROGRAMMING_LANGUAGE,
            name="Python",
            properties={"version": "3.11"},
            confidence=0.7,
            evidence_sources=["SourceA"]
        )
        # Add python (case insensitive) as duplicate
        node2 = EntityNode(
            node_id="lang-py-lower",
            label=EntityType.PROGRAMMING_LANGUAGE,
            name="python",
            properties={"compiled": "no"},
            confidence=0.6,
            evidence_sources=["SourceB"]
        )

        n1_id = self.engine.add_node(self.ws_id, node1)
        n2_id = self.engine.add_node(self.ws_id, node2)

        # Confirm they merged into the original node ID
        self.assertEqual(n1_id, n2_id)
        
        merged_node = self.engine.get_node(self.ws_id, n1_id)
        self.assertIsNotNone(merged_node)
        self.assertEqual(merged_node.name, "Python")  # Preserved shorter/best name
        # Properties merged
        self.assertIn("version", merged_node.properties)
        self.assertIn("compiled", merged_node.properties)
        # Confidence aggregated (1 - (1-0.7)*(1-0.6) = 0.88)
        self.assertAlmostEqual(merged_node.confidence, 0.88, places=2)
        # Evidences unioned
        self.assertIn("SourceA", merged_node.evidence_sources)
        self.assertIn("SourceB", merged_node.evidence_sources)

    def test_semantic_inference_and_gaps(self) -> None:
        """Validates reasoning engine rules (transitive USES and knowledge gaps)."""
        # Ingest Person, Project, and Technology nodes
        person = EntityNode(node_id="p-1", label=EntityType.PERSON, name="Bob", confidence=1.0)
        proj = EntityNode(node_id="proj-1", label=EntityType.PROJECT, name="Project Alpha", confidence=1.0)
        tech = EntityNode(node_id="tech-fastapi", label=EntityType.TECHNOLOGY, name="FastAPI", confidence=1.0)

        self.engine.add_node(self.ws_id, person)
        self.engine.add_node(self.ws_id, proj)
        self.engine.add_node(self.ws_id, tech)

        # Establish Person WORKED_ON Project & Project USES Technology
        rel1 = Relationship(
            relationship_id="r1", source_id="p-1", target_id="proj-1",
            relationship_type=RelationshipType.WORKED_ON, confidence=0.9
        )
        rel2 = Relationship(
            relationship_id="r2", source_id="proj-1", target_id="tech-fastapi",
            relationship_type=RelationshipType.USES, confidence=0.8
        )
        
        self.engine.add_relationship(self.ws_id, rel1)
        self.engine.add_relationship(self.ws_id, rel2)

        # Execute reasoning
        report = self.engine.run_reasoning(self.ws_id)
        
        self.assertEqual(report["inferred_relationships_count"], 1)
        
        # Check newly inferred relationship
        rels = self.engine.list_relationships(self.ws_id)
        inferred_rel = next((r for r in rels if r.relationship_type == RelationshipType.USES and r.source_id == "p-1"), None)
        self.assertIsNotNone(inferred_rel)
        self.assertEqual(inferred_rel.target_id, "tech-fastapi")
        # Propagated confidence: 0.9 * 0.8 * 0.8 (rule penalty) = 0.58
        self.assertAlmostEqual(inferred_rel.confidence, 0.58, places=2)

    def test_path_and_similarity_search(self) -> None:
        """Validates BFS pathfinder and neighbor-based similarity searching."""
        # Set up a chain: A -> B -> C
        n_a = EntityNode(node_id="A", label=EntityType.PERSON, name="Node A")
        n_b = EntityNode(node_id="B", label=EntityType.PROJECT, name="Node B")
        n_c = EntityNode(node_id="C", label=EntityType.TECHNOLOGY, name="Node C")

        self.engine.add_node(self.ws_id, n_a)
        self.engine.add_node(self.ws_id, n_b)
        self.engine.add_node(self.ws_id, n_c)

        r_ab = Relationship(relationship_id="e1", source_id="A", target_id="B", relationship_type=RelationshipType.WORKED_ON)
        r_bc = Relationship(relationship_id="e2", source_id="B", target_id="C", relationship_type=RelationshipType.USES)

        self.engine.add_relationship(self.ws_id, r_ab)
        self.engine.add_relationship(self.ws_id, r_bc)

        # Find paths from A to C
        paths = self.engine.find_paths(self.ws_id, "A", "C", max_depth=3)
        self.assertEqual(len(paths), 1)
        self.assertEqual(len(paths[0]), 2)  # Two edges: A->B, B->C
        self.assertEqual(paths[0][0].relationship_id, "e1")
        self.assertEqual(paths[0][1].relationship_id, "e2")

        # Similarity search
        n_d = EntityNode(node_id="D", label=EntityType.PERSON, name="Node D")
        self.engine.add_node(self.ws_id, n_d)
        r_db = Relationship(relationship_id="e3", source_id="D", target_id="B", relationship_type=RelationshipType.WORKED_ON)
        self.engine.add_relationship(self.ws_id, r_db)

        # A and D both work on B. So they should be similar
        sim = self.engine.search_similar_nodes(self.ws_id, "A", limit=5)
        self.assertTrue(len(sim) > 0)
        self.assertEqual(sim[0][0].node_id, "D")

    def test_large_graph_ingestion_and_ukp_sync(self) -> None:
        """Validates ingestion speed, scalability, and profile sync updates."""
        # 1. Ingest Resume payload
        resume_feed = {
            "user_id": "bob",
            "personal_info": {"full_name": "Bob Vance", "email": "bob@vance.com"},
            "skills": {
                "Python": {"category": "Languages", "confidence_score": 1.0},
                "React": {"category": "Frameworks", "confidence_score": 0.9}
            },
            "projects": [
                {
                    "name": "Vance Refrigerator CRM",
                    "description": "CRM system",
                    "technologies": ["Python", "SQLite"]
                }
            ],
            "experience": [
                {"company": "Vance Refrigeration", "role": "Lead Developer"}
            ]
        }
        self.engine.ingest_resume(self.ws_id, resume_feed)

        # 2. Sync to Unified Knowledge Profile
        profile = KnowledgeProfile(workspace_id=self.ws_id, user_id="bob")
        self.engine.sync_profile(self.ws_id, profile)

        # Assert profile graph is populated
        self.assertIn("person:Bob Vance", profile.knowledge_graph)
        self.assertIn("skill:Python", profile.knowledge_graph["project:Vance Refrigerator CRM"])

    def test_concurrent_updates(self) -> None:
        """Validates graph writes and query lookups are isolated under thread concurrency."""
        exceptions = []

        def worker_writer(idx: int):
            try:
                node = EntityNode(
                    node_id=f"thread-node-{idx}",
                    label=EntityType.TASK,
                    name=f"Task Thread {idx}"
                )
                self.engine.add_node(self.ws_id, node)
            except Exception as e:
                exceptions.append(str(e))

        threads = [threading.Thread(target=worker_writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Concurrent database exceptions: {exceptions}")
        nodes = self.engine.list_nodes(self.ws_id)
        thread_nodes = [n for n in nodes if "thread-node-" in n.node_id]
        self.assertEqual(len(thread_nodes), 10)
