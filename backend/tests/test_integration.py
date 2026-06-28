import json
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app, db_storage


class TestE2EIntegration(unittest.TestCase):
    """End-to-end integration tests verifying the full integrated Nexus AI pipeline."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        # Clear users and workspaces tables for fresh isolation test runs
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

    def test_full_pipeline_flow(self) -> None:
        """Verifies Register -> Login -> Create Workspace -> Upload Document -> Check Health."""
        # 1. Register User
        reg_payload = {
            "username": "test_developer",
            "password": "dev_password123",
            "email": "dev@nexus.ai"
        }
        res_reg = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res_reg.status_code, 200)
        self.assertEqual(res_reg.json()["status"], "success")

        # 2. Login User
        login_payload = {
            "username": "test_developer",
            "password": "dev_password123"
        }
        res_login = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res_login.status_code, 200)
        token = res_login.json()["token"]
        self.assertTrue(token.startswith("token_for_test_developer"))

        # 3. Create Workspace
        ws_payload = {
            "name": "Integration Test Workspace"
        }
        res_ws = self.client.post("/api/workspaces?user_id=test_developer", json=ws_payload)
        self.assertEqual(res_ws.status_code, 200)
        workspace_id = res_ws.json()["workspace"]["workspace_id"]
        self.assertTrue(workspace_id.startswith("ws-"))

        # 4. Upload Document
        files = {
            "file": ("sample.txt", b"Nexus AI is a local agent orchestrator pipeline framework.", "text/plain")
        }
        res_upload = self.client.post(f"/api/documents/upload?workspace_id={workspace_id}", files=files)
        self.assertEqual(res_upload.status_code, 200)
        self.assertTrue(res_upload.json()["document_id"].startswith("doc-"))

        # 5. Check Ingested Documents
        res_docs = self.client.get(f"/api/documents?workspace_id={workspace_id}")
        self.assertEqual(res_docs.status_code, 200)
        docs = res_docs.json()["documents"]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["name"], "sample.txt")
        self.assertEqual(docs[0]["status"], "indexed")

        # 6. Check Health Dashboard
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)
        self.assertEqual(res_health.json()["status"], "healthy")
        self.assertTrue(res_health.json()["services"]["ollama_provider"])
