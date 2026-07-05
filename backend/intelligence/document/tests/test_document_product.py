"""End-to-end integration tests validating Document Ingestion, Querying, Summaries, and History Diffs."""

import time
import unittest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.document_service import DocumentHistoryManager


class TestDocumentProduct(unittest.TestCase):
    """E2E Integration tests validating Document Intelligence REST endpoints and workflows."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.cache = DocumentCache()
        self.history_manager = DocumentHistoryManager()
        # Reset cached entities
        self.cache._documents.clear()
        self.cache._reports.clear()
        self.cache._jobs.clear()

    def test_single_markdown_upload_and_analyze(self) -> None:
        """Validates standard Markdown ingestion, parsing, metadata, and summarization."""
        # 1. Upload Markdown document
        md_content = "# Guide to Nexus AI\nNexus AI is built by OpenAI and Microsoft in London.\nDesigned a server architecture."
        files = {"file": ("guide.md", md_content, "text/markdown")}
        
        resp_upload = self.client.post("/document/upload", files=files)
        self.assertEqual(resp_upload.status_code, 200)
        upload_data = resp_upload.json()
        doc_id = upload_data["document_id"]
        self.assertEqual(upload_data["filename"], "guide.md")
        self.assertIsNotNone(doc_id)

        # 2. Trigger synchronous analysis
        payload = {
            "workspace_id": "ws-md",
            "document_ids": [doc_id]
        }
        resp_analyze = self.client.post("/document/analyze", json=payload)
        self.assertEqual(resp_analyze.status_code, 200)
        report = resp_analyze.json()

        # 3. Verify metadata & entities & summary
        meta = report["metadata"][doc_id]
        self.assertEqual(meta["title"], "Guide to Nexus AI")
        self.assertEqual(meta["format"], "MD")
        self.assertGreater(meta["word_count"], 0)
        self.assertIn("nexus", meta["keywords"])

        self.assertIsNotNone(report["summary"]["executive"])
        self.assertIsNotNone(report["summary"]["technical"])
        self.assertGreater(len(report["summary"]["bullet"]), 0)

        # Verify entity extraction matches (London, OpenAI, Microsoft, etc.)
        extracted_entities = [e["name"] for e in report["entities"]]
        self.assertIn("London", extracted_entities)
        self.assertIn("OpenAI", extracted_entities)
        
        # Verify knowledge extraction
        self.assertTrue(any(item["category"] == "Project" for item in report["extracted_knowledge"]))

    def test_multiple_mixed_documents_similarity(self) -> None:
        """Uploads multiple files (DOCX, JSON, CSV) and verifies Jaccard similarity mapping."""
        # 1. Upload DOCX (mock)
        resp_docx = self.client.post(
            "/document/upload",
            files={"file": ("project.docx", b"binary content word", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        )
        doc_id1 = resp_docx.json()["document_id"]

        # 2. Upload CSV
        csv_content = "Name,Language,Category\nAlice,Python,Backend\nBob,React,Frontend"
        resp_csv = self.client.post(
            "/document/upload",
            files={"file": ("team.csv", csv_content, "text/csv")}
        )
        doc_id2 = resp_csv.json()["document_id"]

        # 3. Upload JSON
        json_content = '{"title": "Nexus System", "technologies": ["Python", "React", "Docker"]}'
        resp_json = self.client.post(
            "/document/upload",
            files={"file": ("system.json", json_content, "application/json")}
        )
        doc_id3 = resp_json.json()["document_id"]

        # 4. Trigger synchronous multi-document analysis
        payload = {
            "workspace_id": "ws-multi",
            "document_ids": [doc_id1, doc_id2, doc_id3]
        }
        resp_analyze = self.client.post("/document/analyze", json=payload)
        self.assertEqual(resp_analyze.status_code, 200)
        report = resp_analyze.json()

        self.assertEqual(len(report["document_ids"]), 3)
        self.assertIn(doc_id1, report["metadata"])
        self.assertIn(doc_id2, report["metadata"])
        self.assertIn(doc_id3, report["metadata"])

        # Check Jaccard similarities
        self.assertGreater(len(report["similar_documents"]), 0)
        for mapping in report["similar_documents"]:
            self.assertIsNotNone(mapping["similarity_score"])
            self.assertIn(mapping["target_document_id"], [doc_id1, doc_id2, doc_id3])

    def test_async_workflow_for_large_pdf(self) -> None:
        """Validates the asynchronous flow with thread execution ticks and status tracking."""
        resp_upload = self.client.post(
            "/document/upload",
            files={"file": ("large_doc.pdf", b"pdf mock stream contents regarding Python design", "application/pdf")}
        )
        doc_id = resp_upload.json()["document_id"]

        payload = {
            "workspace_id": "ws-async",
            "document_ids": [doc_id],
            "options": {"async": True}
        }
        resp_analyze = self.client.post("/document/analyze", json=payload)
        self.assertEqual(resp_analyze.status_code, 200)
        job_data = resp_analyze.json()
        job_id = job_data["job_id"]
        self.assertEqual(job_data["status"], "processing")
        self.assertIsNotNone(job_id)

        # Poll job status
        for _ in range(10):
            time.sleep(0.5)
            status_resp = self.client.get(f"/document/status/{job_id}")
            self.assertEqual(status_resp.status_code, 200)
            status_data = status_resp.json()
            if status_data["status"] in ("completed", "failed"):
                break

        self.assertEqual(status_data["status"], "completed")
        self.assertEqual(status_data["progress"], 100)
        report_id = status_data["report_id"]

        # Retrieve final report
        resp_report = self.client.get(f"/document/report/{report_id}")
        self.assertEqual(resp_report.status_code, 200)
        report = resp_report.json()
        self.assertEqual(report["report_id"], report_id)

    def test_citation_aware_query(self) -> None:
        """Verifies answering queries with citation pointer mappings."""
        # 1. Ingest document
        doc_text = "# Project Alpha\nThis project implements a secure authentication system in React.\n# Project Beta\nThis project implements a billing gateway in Python."
        resp_upload = self.client.post(
            "/document/upload",
            files={"file": ("projects.md", doc_text, "text/markdown")}
        )
        doc_id = resp_upload.json()["document_id"]

        # Run analysis to build cache
        self.client.post("/document/analyze", json={
            "workspace_id": "ws-query",
            "document_ids": [doc_id]
        })

        # 2. Query document collection
        query_payload = {
            "workspace_id": "ws-query",
            "document_ids": [doc_id],
            "query": "Where does it mention authentication in React?",
            "options": {"limit": 2}
        }
        resp_query = self.client.post("/document/query", json=query_payload)
        self.assertEqual(resp_query.status_code, 200)
        query_data = resp_query.json()
        
        self.assertIn("authentication", query_data["answer"].lower())
        self.assertGreater(len(query_data["citations"]), 0)
        
        cit = query_data["citations"][0]
        self.assertEqual(cit["document_id"], doc_id)
        self.assertEqual(cit["document_name"], "projects.md")
        self.assertIn("authentication", cit["text_chunk"].lower())

    def test_pipeline_recovery_and_history_comparison(self) -> None:
        """Verifies history tracking logs and delta comparisons of versions."""
        # First version
        v1_text = "Standard introduction text."
        doc_1 = self.client.post("/document/upload", files={"file": ("doc.txt", v1_text, "text/plain")}).json()["document_id"]
        r1 = self.client.post("/document/analyze", json={"workspace_id": "ws-history", "document_ids": [doc_1]}).json()
        report_id_1 = r1["report_id"]

        # Second version
        v2_text = "Standard introduction text.\nWith additional paragraphs and keywords like FastAPI, FastAPI, FastAPI, Python, and Docker."
        doc_2 = self.client.post("/document/upload", files={"file": ("doc.txt", v2_text, "text/plain")}).json()["document_id"]
        r2 = self.client.post("/document/analyze", json={"workspace_id": "ws-history", "document_ids": [doc_2]}).json()
        report_id_2 = r2["report_id"]

        # Retrieve history
        hist_resp = self.client.get("/document/history?workspace_id=ws-history")
        self.assertEqual(hist_resp.status_code, 200)
        history = hist_resp.json()["history"]
        self.assertGreaterEqual(len(history), 2)

        # Retrieve comparison
        comp_resp = self.client.get(f"/document/compare?base_id={report_id_1}&target_id={report_id_2}")
        self.assertEqual(comp_resp.status_code, 200)
        comp = comp_resp.json()

        self.assertEqual(comp["base_report_id"], report_id_1)
        self.assertEqual(comp["target_report_id"], report_id_2)
        
        # Word counts delta
        self.assertGreater(comp["comparison"]["word_count"]["delta"], 0)
        self.assertIn("fastapi", comp["comparison"]["keywords"]["added"])
