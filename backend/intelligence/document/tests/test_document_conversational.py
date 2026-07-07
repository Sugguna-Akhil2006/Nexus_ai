"""Integration tests validating conversational document workflows, citations, memory, and reasoning."""

import time
import uuid
import threading
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.workspace_memory import WorkspaceMemory
from backend.intelligence.document.document_session import DocumentSessionManager


class TestDocumentConversational(unittest.TestCase):
    """Integration test suite validating conversational engine REST endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.cache = DocumentCache()
        self.memory = WorkspaceMemory()
        self.session_manager = DocumentSessionManager()
        
        # Reset local cache memories between test cases
        self.cache._documents.clear()
        self.cache._reports.clear()
        self.cache._jobs.clear()
        self.memory.clear_cache("ws-conv")
        self.memory.clear_cache("ws-large")

    def test_single_document_qa_with_citations(self) -> None:
        """Validates simple Q&A queries over a single uploaded document, checking citations."""
        # 1. Ingest file
        doc_content = "# Project Delta\nNexus is developed in React.\nAuthentication uses JSON Web Tokens."
        resp_upload = self.client.post(
            "/document/upload",
            files={"file": ("project_delta.md", doc_content.encode("utf-8"), "text/markdown")}
        )
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        # Run analysis to initialize indices
        self.client.post("/document/analyze", json={
            "workspace_id": "ws-conv",
            "document_ids": [doc_id]
        })

        # 2. Chat query
        payload = {
            "workspace_id": "ws-conv",
            "query": "Which language is used in Project Delta?",
            "document_ids": [doc_id]
        }
        resp_chat = self.client.post("/document/chat", json=payload)
        self.assertEqual(resp_chat.status_code, 200)
        res = resp_chat.json()

        # Check conversation response structure
        self.assertIsNotNone(res["answer"])
        self.assertIsNotNone(res["summary"])
        self.assertIsNotNone(res["evidence"])
        self.assertGreater(len(res["citations"]), 0)
        self.assertEqual(res["citations"][0]["document_id"], doc_id)
        self.assertEqual(res["citations"][0]["document_name"], "project_delta.md")
        self.assertIsNotNone(res["citations"][0]["chunk_id"])
        self.assertIsNotNone(res["citations"][0]["confidence"])
        self.assertIsNotNone(res["citations"][0]["evidence"])
        self.assertIn("project_delta.md", res["related_documents"])
        self.assertGreater(len(res["suggested_follow_up_questions"]), 0)

    def test_multi_document_cross_reasoning(self) -> None:
        """Validates reasoning queries across multiple document version logs."""
        # Upload doc v1
        doc1_content = "# Project Alpha v1\nThe gateway is written in Python.\nDatabase is SQLite."
        doc_id1 = self.client.post(
            "/document/upload",
            files={"file": ("doc_v1.md", doc1_content.encode("utf-8"), "text/markdown")}
        ).json()["document_id"]

        # Upload doc v2
        doc2_content = "# Project Alpha v2\nThe gateway is written in Python.\nAdded Docker container and FastAPI framework."
        doc_id2 = self.client.post(
            "/document/upload",
            files={"file": ("doc_v2.md", doc2_content.encode("utf-8"), "text/markdown")}
        ).json()["document_id"]

        # Sync analysis
        self.client.post("/document/analyze", json={
            "workspace_id": "ws-conv",
            "document_ids": [doc_id1, doc_id2]
        })

        # 1. Ask technology check query
        payload_tech = {
            "workspace_id": "ws-conv",
            "query": "What technologies are common?",
            "document_ids": [doc_id1, doc_id2]
        }
        res_tech = self.client.post("/document/chat", json=payload_tech).json()
        self.assertIn("Python", res_tech["answer"])

        # 2. Ask delta query
        payload_diff = {
            "workspace_id": "ws-conv",
            "query": "What changed between version 1 and version 2?",
            "document_ids": [doc_id1, doc_id2]
        }
        res_diff = self.client.post("/document/chat", json=payload_diff).json()
        self.assertIn("Fastapi", res_diff["answer"])
        self.assertIn("Docker", res_diff["answer"])

    def test_conversation_continuation(self) -> None:
        """Verifies session history retention and follow-up prompts using context window."""
        doc_content = "# System Info\nNexus server runs on port 8000."
        doc_id = self.client.post(
            "/document/upload",
            files={"file": ("sys_info.md", doc_content.encode("utf-8"), "text/markdown")}
        ).json()["document_id"]

        self.client.post("/document/analyze", json={
            "workspace_id": "ws-conv",
            "document_ids": [doc_id]
        })

        # Turn 1
        conv_id = f"test-sess-{str(uuid.uuid4())[:8]}"
        res1 = self.client.post("/document/chat", json={
            "workspace_id": "ws-conv",
            "conversation_id": conv_id,
            "query": "What port does the server run on?",
            "document_ids": [doc_id]
        }).json()
        self.assertIn("8000", res1["answer"])

        # Turn 2: Retrieve history via GET
        hist_resp = self.client.get(f"/document/conversation/{conv_id}")
        self.assertEqual(hist_resp.status_code, 200)
        messages = hist_resp.json()["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

        # Turn 3: Follow-up question referencing previous context
        res2 = self.client.post("/document/chat", json={
            "workspace_id": "ws-conv",
            "conversation_id": conv_id,
            "query": "Can you summarize that port setting details?",
            "document_ids": [doc_id]
        }).json()
        self.assertIsNotNone(res2["answer"])

    def test_empty_workspace_and_search_retrievals(self) -> None:
        """Tests queries on empty workspaces or document lists, verifying fallback safety."""
        # Query empty workspace
        payload = {
            "workspace_id": "ws-empty",
            "query": "Where is SQLite configured?",
            "document_ids": []
        }
        res = self.client.post("/document/chat", json=payload).json()
        self.assertIsNotNone(res["answer"])
        self.assertEqual(len(res["citations"]), 0)

        # Search index directly via REST POST
        search_req = {
            "workspace_id": "ws-empty",
            "query": "authentication",
            "search_mode": "KEYWORD",
            "limit": 3
        }
        search_resp = self.client.post("/document/search", json=search_req)
        self.assertEqual(search_resp.status_code, 200)
        self.assertEqual(len(search_resp.json()["results"]), 0)

    def test_concurrent_sessions(self) -> None:
        """Launches parallel worker threads executing chat turns to confirm session locks isolation."""
        # 1. Ingest file
        doc_content = "# Concurrent Doc\nProcess threads safely isolation test."
        doc_id = self.client.post(
            "/document/upload",
            files={"file": ("concurrent.md", doc_content.encode("utf-8"), "text/markdown")}
        ).json()["document_id"]

        self.client.post("/document/analyze", json={
            "workspace_id": "ws-conv",
            "document_ids": [doc_id]
        })

        conv_id = f"concurrent-{str(uuid.uuid4())[:8]}"
        exceptions = []

        def worker_turn():
            try:
                resp = self.client.post("/document/chat", json={
                    "workspace_id": "ws-conv",
                    "conversation_id": conv_id,
                    "query": "Is thread safety verified?",
                    "document_ids": [doc_id]
                })
                if resp.status_code != 200:
                    exceptions.append(f"Status code {resp.status_code}")
            except Exception as e:
                exceptions.append(str(e))

        threads = [threading.Thread(target=worker_turn) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Thread safety exceptions occurred: {exceptions}")
