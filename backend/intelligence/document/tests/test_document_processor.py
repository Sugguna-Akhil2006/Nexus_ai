"""Integration tests validating the core Intelligent Document Processing Engine."""

import unittest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.similarity_engine import DocumentSimilarityEngine
from backend.intelligence.document.document_graph import DocumentGraphBuilder
from backend.intelligence.document.models import EntityNode, RelationshipEdge


class TestDocumentProcessor(unittest.TestCase):
    """Verifies entity extraction, classifications, graphs, and indexes."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.cache = DocumentCache()
        self.cache._documents.clear()
        self.cache._reports.clear()

    def test_technical_markdown_reasoning(self) -> None:
        """Verifies full IDP parsing, entity naming, graphs, and knowledge extraction on technical MD."""
        # 1. Ingest document
        md_text = """
# System Guide
This project implements a secure authentication system in React.
We deploy the Docker container to a Kubernetes cluster for scale.
The codebase is written in Python, using the FastAPI framework.
John Doe is the lead engineer designed this architecture.
        """
        resp_upload = self.client.post(
            "/document/upload",
            files={"file": ("guide.md", md_text, "text/markdown")}
        )
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        # 2. Deep processing
        payload = {
            "workspace_id": "ws-idp",
            "document_ids": [doc_id],
            "options": {
                "custom_categories": ["Cybersecurity", "Cloud"]
            }
        }
        resp_process = self.client.post("/document/process", json=payload)
        self.assertEqual(resp_process.status_code, 200)
        report = resp_process.json()

        # Check metadata
        self.assertEqual(report["metadata"][doc_id]["title"], "System Guide")
        self.assertEqual(report["metadata"][doc_id]["format"], "MD")

        # Entity validations (React, Docker, Kubernetes, Python, FastAPI, John Doe)
        extracted_entities = {e["name"].lower(): e["category"] for e in report["entities"]}
        self.assertIn("react", extracted_entities)
        self.assertEqual(extracted_entities["react"], "Frameworks")
        self.assertIn("python", extracted_entities)
        self.assertEqual(extracted_entities["python"], "Programming Languages")
        self.assertIn("fastapi", extracted_entities)
        self.assertEqual(extracted_entities["fastapi"], "Frameworks")
        self.assertIn("kubernetes", extracted_entities)
        self.assertEqual(extracted_entities["kubernetes"], "Technologies")
        self.assertIn("john doe", extracted_entities)
        self.assertEqual(extracted_entities["john doe"], "People")

        # Classification checks (Software Engineering, Cloud, Cybersecurity, etc.)
        classified_topics = {t["name"] for t in report["topics"]}
        self.assertIn("Software Engineering", classified_topics)
        self.assertIn("Cloud", classified_topics)

        # Graph relationship checks
        edges = {(e["source"].lower(), e["target"].lower(), e["relationship_type"]) for e in report["relationships"]}
        # FastAPI -> Python (written_in)
        self.assertTrue(
            any(s == "fastapi" and t == "python" and r == "written_in" for s, t, r in edges)
        )
        # Docker -> Kubernetes (deploys_to)
        self.assertTrue(
            any(s == "docker" and t == "kubernetes" and r == "deploys_to" for s, t, r in edges)
        )

        # Knowledge object check
        self.assertGreater(len(report["knowledge_objects"]), 0)
        obj = report["knowledge_objects"][0]
        self.assertIsNotNone(obj["title"])
        self.assertIsNotNone(obj["evidence"])
        self.assertGreater(obj["confidence"], 0.5)

    def test_semantic_index_concept_search(self) -> None:
        """Verifies inverted semantic index matching for concepts, entities, and citations."""
        text = """
# Research Paper
We study PyTorch machine learning models.
We perform training on large GPU clusters.
# Appendix A
Refer to Appendix A.
        """
        doc_id = self.client.post(
            "/document/upload",
            files={"file": ("paper.md", text, "text/markdown")}
        ).json()["document_id"]

        report = self.client.post("/document/process", json={
            "workspace_id": "ws-research",
            "document_ids": [doc_id]
        }).json()
        report_id = report["report_id"]

        # Search Concept: "pytorch"
        s_payload = {
            "report_id": report_id,
            "search_type": "concept",
            "query": "pytorch"
        }
        resp = self.client.post("/document/index/search", json=s_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.json()), 0)
        self.assertIn("pytorch", resp.json()[0].lower())

        # Search Entity: "PyTorch"
        se_payload = {
            "report_id": report_id,
            "search_type": "entity",
            "query": "pytorch"
        }
        resp_ent = self.client.post("/document/index/search", json=se_payload)
        self.assertEqual(resp_ent.status_code, 200)
        self.assertGreater(len(resp_ent.json()), 0)

        # Search Citation: "Appendix A"
        sc_payload = {
            "report_id": report_id,
            "search_type": "citation",
            "query": "Appendix A"
        }
        resp_cit = self.client.post("/document/index/search", json=sc_payload)
        self.assertEqual(resp_cit.status_code, 200)
        self.assertGreater(len(resp_cit.json()), 0)

    def test_similarity_duplicate_and_near_duplicate(self) -> None:
        """Verifies duplicate and near-duplicate detections."""
        engine = DocumentSimilarityEngine()
        t1 = "FastAPI builds scalable microservices in Python."
        t2 = "FastAPI builds scalable microservices in Python."
        t3 = "FastAPI builds highly scalable microservices on Docker containers with Python code."
        t4 = "Entirely unrelated billing text about financial transactions."

        # Identical
        self.assertTrue(engine.is_duplicate(t1, t2))
        self.assertFalse(engine.is_duplicate(t1, t3))

        # Near duplicates
        self.assertTrue(engine.is_near_duplicate(t1, t3, threshold=0.4))
        self.assertFalse(engine.is_near_duplicate(t1, t4, threshold=0.4))

    def test_directed_graph_builder_and_walk(self) -> None:
        """Validates directed graph structure builds and DFS path walks."""
        builder = DocumentGraphBuilder()
        nodes = [
            EntityNode(name="FastAPI", category="Frameworks", confidence=1.0),
            EntityNode(name="Python", category="Programming Languages", confidence=0.9),
            EntityNode(name="Docker", category="Technologies", confidence=0.9)
        ]
        edges = [
            RelationshipEdge(source="FastAPI", target="Python", relationship_type="written_in", confidence=0.9),
            RelationshipEdge(source="Python", target="Docker", relationship_type="uses", confidence=0.8)
        ]
        graph = builder.build_graph(nodes, edges)

        # outgoing edges
        out_edges = builder.get_outgoing_connections(graph, "FastAPI")
        self.assertEqual(len(out_edges), 1)
        self.assertEqual(out_edges[0].target, "Python")

        # path search: FastAPI -> Python -> Docker
        path = builder.find_path(graph, "FastAPI", "Docker")
        self.assertEqual(path, ["FastAPI", "Python", "Docker"])
