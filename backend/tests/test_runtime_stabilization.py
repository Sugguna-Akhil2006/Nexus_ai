import unittest
import uuid
import time
from datetime import datetime
from fastapi.testclient import TestClient

from backend.api.main import app, db_storage, METRICS_CACHE


class TestRuntimeStabilization(unittest.TestCase):
    """Regression test suite for Runtime MVP stabilization, RAG quality, and diagnostics."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Clear relational database tables for fresh, isolated workspace contexts
        conn = db_storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users")
        cursor.execute("DELETE FROM workspaces")
        cursor.execute("DELETE FROM members")
        cursor.execute("DELETE FROM documents")
        cursor.execute("DELETE FROM conversations")
        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()

        # Seed test user and workspace
        self.username = "stabilization_tester"
        self.client.post("/api/auth/register", json={
            "username": self.username,
            "password": "pass_stabilize_123",
            "email": "tester@nexus.ai"
        })
        res_ws = self.client.post("/api/workspaces?user_id=stabilization_tester", json={
            "name": "Stabilization Workspace"
        })
        self.workspace_id = res_ws.json()["workspace"]["workspace_id"]

    def test_semantic_chunking_resume(self) -> None:
        """Task 3: Verify semantic chunking strategy correctly parses resume sections."""
        resume_content = (
            "John Doe Resume\n\n"
            "EDUCATION\n"
            "B.Sc. Computer Science from Stanford University, 2021.\n\n"
            "SKILLS\n"
            "Expert in Python, PyTorch, FastAPI, and Docker.\n\n"
            "EXPERIENCE\n"
            "Software Engineer at Google (2021 - Present). Built RAG search engines.\n\n"
            "PROJECTS\n"
            "NexusAI - Multi-agent framework with intent routing and local LLM.\n"
        )
        
        # Upload as a text resume
        res = self.client.post(
            f"/api/documents/upload?workspace_id={self.workspace_id}",
            files={"file": ("resume.txt", resume_content.encode("utf-8"), "text/plain")}
        )
        self.assertEqual(res.status_code, 200)
        doc_id = res.json()["document_id"]
        
        # Verify metrics were stored in METRICS_CACHE
        self.assertIn(doc_id, METRICS_CACHE)
        self.assertGreater(METRICS_CACHE[doc_id]["extraction_time"], 0.0)
        self.assertGreater(METRICS_CACHE[doc_id]["chunking_time"], 0.0)
        self.assertGreater(METRICS_CACHE[doc_id]["embedding_time"], 0.0)

        # Trigger RAG query via WebSocket and verify intent classifier & section mapping
        with self.client.websocket_connect("/api/chat/ws") as ws:
            ws.send_json({
                "action": "send_message",
                "conversation_id": "test-conv-resume",
                "workspace_id": self.workspace_id,
                "user_id": self.username,
                "message": "What is John Doe's education background and programming skills?",
                "retrieval_options": {"enable_search": True}
            })
            
            # Read messages until we get final metadata
            final_metadata = None
            for _ in range(1000):
                resp = ws.receive_json()
                if "metadata" in resp:
                    final_metadata = resp["metadata"]
                    break
            
            self.assertIsNotNone(final_metadata)
            self.assertEqual(final_metadata["current_workflow"], "Resume Review")
            self.assertEqual(final_metadata["embedding_model"], "nomic-embed-text")
            
            # Check RAG Debugger details (Task 4)
            chunks = final_metadata["retrieved_chunks"]
            self.assertGreater(len(chunks), 0)
            
            # Education or Skills section name should be parsed semantically
            sections = [c["section_name"] for c in chunks]
            self.assertTrue(any("Education" in s or "Skills" in s or "Experience" in s for s in sections))
            
            # Check prompt diagnostics (Task 5)
            diag = final_metadata["prompt_diagnostics"]
            self.assertGreater(diag["retrieved_chunk_count"], 0)
            self.assertIn("Resume Review", diag["system_prompt"])
            self.assertTrue(
                "Stanford" in diag["final_assembled_prompt"] or 
                "NexusAI" in diag["final_assembled_prompt"] or 
                "FastAPI" in diag["final_assembled_prompt"]
            )

    def test_semantic_chunking_research_paper(self) -> None:
        """Task 3: Verify semantic chunking parses research paper abstract and methodology sections."""
        paper_content = (
            "Deep Learning Research Paper\n\n"
            "ABSTRACT\n"
            "This paper explores semantic chunking strategies for low-latency RAG execution on small GPUs.\n\n"
            "INTRODUCTION\n"
            "Information retrieval has become standard in modern agent stacks.\n\n"
            "METHODOLOGY\n"
            "We propose splitting documents dynamically using structured regular expression boundaries.\n\n"
            "RESULTS\n"
            "Our semantic splitting reduces LLM response latency by 23%.\n\n"
            "CONCLUSION\n"
            "Dynamic headings parsing outperforms fixed boundaries.\n"
        )
        
        res = self.client.post(
            f"/api/documents/upload?workspace_id={self.workspace_id}",
            files={"file": ("paper.txt", paper_content.encode("utf-8"), "text/plain")}
        )
        self.assertEqual(res.status_code, 200)
        
        with self.client.websocket_connect("/api/chat/ws") as ws:
            ws.send_json({
                "action": "send_message",
                "conversation_id": "test-conv-paper",
                "workspace_id": self.workspace_id,
                "user_id": self.username,
                "message": "What methodology was used in this research?",
                "retrieval_options": {"enable_search": True}
            })
            
            final_metadata = None
            for _ in range(1000):
                resp = ws.receive_json()
                if "metadata" in resp:
                    final_metadata = resp["metadata"]
                    break
            
            self.assertIsNotNone(final_metadata)
            # Should map to Research Assistant intent
            self.assertEqual(final_metadata["current_workflow"], "Research Assistant")
            
            # Check parsed headings
            sections = [c["section_name"] for c in final_metadata["retrieved_chunks"]]
            self.assertTrue(any("Methodology" in s or "Abstract" in s or "Introduction" in s for s in sections))

    def test_no_hallucinations_on_missing_context(self) -> None:
        """Task 1 & 7: Verify that Document QA template refuses to fabricate answers when context is missing."""
        doc_content = "This document only discusses cooking standard Italian pasta recipes."
        
        self.client.post(
            f"/api/documents/upload?workspace_id={self.workspace_id}",
            files={"file": ("cooking.txt", doc_content.encode("utf-8"), "text/plain")}
        )
        
        with self.client.websocket_connect("/api/chat/ws") as ws:
            ws.send_json({
                "action": "send_message",
                "conversation_id": "test-conv-cooking",
                "workspace_id": self.workspace_id,
                "user_id": self.username,
                "message": "What is the capital of France according to the document?",
                "retrieval_options": {"enable_search": True}
            })
            
            tokens = []
            final_metadata = None
            for _ in range(1000):
                resp = ws.receive_json()
                if "token" in resp:
                    tokens.append(resp["token"])
                if "metadata" in resp:
                    final_metadata = resp["metadata"]
                    break
            
            response_text = "".join(tokens)
            # Response should contain the template constraint indicating the information is missing
            self.assertTrue(
                "cannot" in response_text.lower() or 
                "not found" in response_text.lower() or 
                "not provide" in response_text.lower() or
                "not contain" in response_text.lower() or
                "don't have" in response_text.lower()
            )

    def test_empty_and_corrupted_document(self) -> None:
        """Task 7: Verify empty/corrupted uploads do not crash the system."""
        # 1. Empty document upload
        res_empty = self.client.post(
            f"/api/documents/upload?workspace_id={self.workspace_id}",
            files={"file": ("empty.txt", b"", "text/plain")}
        )
        # Should raise 422 Unprocessable Entity
        self.assertEqual(res_empty.status_code, 422)
        
        # 2. Corrupted PDF upload
        corrupt_pdf_content = b"%PDF-1.4\n%invalid_pdf_data\n%%EOF"
        res_corrupt = self.client.post(
            f"/api/documents/upload?workspace_id={self.workspace_id}",
            files={"file": ("corrupt.pdf", corrupt_pdf_content, "application/pdf")}
        )
        # Fallback to plain decoding should handle it gracefully without API crashing
        self.assertEqual(res_corrupt.status_code, 200)
