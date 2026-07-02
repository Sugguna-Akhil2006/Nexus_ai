"""Integration tests for the Intelligence API Gateway routing and endpoint validations."""

from concurrent.futures import ThreadPoolExecutor
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.intelligence.router import router
from backend.api.intelligence.responses import GatewayExecutionResponse
from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.resume.module import ResumeModule


class TestAPIGateway(unittest.TestCase):
    """Verifies capabilities routing, input checks, modules lists, and multi-thread concurrency."""

    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

        # Register ResumeModule
        self.registry = IntelligenceRegistry()
        self.registry.register(ResumeModule())

    def test_resume_analysis_endpoint(self) -> None:
        """Verifies standard resume execute routing matches and returns 200 OK."""
        payload = {
            "workspace_id": "ws-gw-test",
            "capability": "RESUME_PARSING",
            "metadata": {
                "resume": {
                    "personal_info": {"full_name": "Bob Vance", "email": "bob@vance.com"},
                    "skills": [{"name": "Sales"}]
                },
                "filename": "vance.txt"
            }
        }
        response = self.client.post("/api/intelligence/execute", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "completed")
        self.assertEqual(data["module"], "ResumeIntelligence")
        self.assertIn("unified_report", data["data"])

    def test_unknown_module(self) -> None:
        """Verifies searching an unregistered capability returns 404 NOT FOUND."""
        payload = {
            "workspace_id": "ws-gw-test",
            "capability": "GITHUB_INTELLIGENCE"
        }
        response = self.client.post("/api/intelligence/execute", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No registered module supports capability", response.json()["detail"])

    def test_invalid_request(self) -> None:
        """Verifies bad inputs or empty string workspace checks trigger validation errors."""
        # Missing workspace_id parameter
        payload = {
            "capability": "RESUME_PARSING"
        }
        response = self.client.post("/api/intelligence/execute", json=payload)
        self.assertEqual(response.status_code, 422)

        # Whitespace workspace_id parameter
        payload = {
            "workspace_id": "   ",
            "capability": "RESUME_PARSING"
        }
        response = self.client.post("/api/intelligence/execute", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Workspace ID must not be empty", response.json()["detail"])

    def test_modules_list_endpoint(self) -> None:
        """Verifies list route returns modules listing array."""
        response = self.client.get("/api/intelligence/modules")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("ResumeIntelligence", data["modules"])
        self.assertIn("RESUME_PARSING", data["capabilities"])

    def test_concurrent_requests(self) -> None:
        """Verifies concurrent multi-threaded requests are handled correctly."""
        payload = {
            "workspace_id": "ws-gw-concurrent",
            "capability": "RESUME_PARSING",
            "metadata": {
                "resume": {
                    "personal_info": {"full_name": "Bob Vance"}
                }
            }
        }

        def make_call() -> int:
            res = self.client.post("/api/intelligence/execute", json=payload)
            return res.status_code

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_call) for _ in range(4)]
            for f in futures:
                self.assertEqual(f.result(), 200)
