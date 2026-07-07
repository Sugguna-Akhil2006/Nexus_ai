"""Tests for the Resume Intelligence Platform.

Verifies the 6 Prompt 37 analytical tools, event dispatches, 
database persistence tables, and HTTP API controllers.
"""

from io import BytesIO
import json
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.resume_service import ResumeOrchestrationService
from backend.tools.tool import ToolRegistry, ToolRequest, ToolResponse
from backend.runtime.event import Event, EventBus, EventType
from backend.api.sqlite_mock import DBStorage

class TestResumePlatform(unittest.TestCase):
    """Test suite covering tools execution, database writes, events, and API endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.tool_registry = ToolRegistry()
        self.workspace_id = "ws-prompt37-test"
        self.user_id = "admin"
        self.db = DBStorage()

        # Setup Mock Model Provider
        from backend.interfaces.model import ModelRegistry
        from backend.agents.chat import MockChatModelProvider
        self.model_registry = ModelRegistry()
        with self.model_registry._lock:
            self.model_registry._providers.clear()
        self.model_provider = MockChatModelProvider()
        self.model_registry.register_provider("mock_chat", self.model_provider)

        # Setup Mock Vector Provider
        from backend.interfaces.vector import VectorRegistry
        from backend.providers.qdrant_vector import QdrantVectorProvider
        self.vector_registry = VectorRegistry()
        with self.vector_registry._lock:
            self.vector_registry._providers.clear()
        self.vector_registry.register_provider("qdrant", QdrantVectorProvider(mock=True))

        # Setup Event Listener to catch custom events
        self.event_bus = EventBus()
        self.caught_events = []
        self.event_bus.subscribe("*", self.catch_event)

        # Register default test data
        self.mock_resume_text = (
            "Jane Doe\n"
            "Email: jane.doe@example.com\n"
            "Phone: 123-456-7890\n"
            "Skills: Python, FastAPI, Docker, communication\n"
            "Experience:\n"
            "- Senior Software Engineer, 5 years. Reduced latency by 40%.\n"
            "Education:\n"
            "- B.S. in Computer Science, Tier-1 graduated."
        )
        self.mock_jd = "Looking for a Python Developer with FastAPI and Docker skills. Kubernetes is a plus."

    def catch_event(self, event: Event) -> None:
        """Callback to store published events."""
        if event.payload:
            name = event.payload.get("event_name") or event.payload.get("event")
            if name:
                self.caught_events.append(name)

    def test_tools_registration(self) -> None:
        """Verifies the 6 Prompt 37 tools are registered in the registry."""
        expected_tools = [
            "resume_parser", "ats_scoring", "job_matcher", 
            "skill_gap", "resume_comparison", "resume_report"
        ]
        registered = [t.schema.tool_id for t in self.tool_registry.list_tools()]
        for t in expected_tools:
            self.assertIn(t, registered, f"Tool '{t}' is not registered in the ToolRegistry.")

    def test_database_records_creation(self) -> None:
        """Verifies SQL helpers read/write resumes, ATS sheets, analysis reports, and comparisons."""
        # 1. Test Resumes Metadata Write/Read
        self.db.create_resume_metadata(
            document_id="doc-db-test",
            workspace_id=self.workspace_id,
            name="Alice Cooper",
            email="alice@cooper.com",
            skills=json.dumps(["Java", "Spring Boot"])
        )
        meta = self.db.get_resume_metadata("doc-db-test")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["name"], "Alice Cooper")
        self.assertEqual(meta["email"], "alice@cooper.com")
        self.assertIn("Java", json.loads(meta["skills"]))

        # 2. Test ATS Report Write/Read
        self.db.create_ats_report(
            ats_id="ats-db-test",
            document_id="doc-db-test",
            score=92,
            report_data=json.dumps({"ats_score": 92, "recommendations": []})
        )
        ats = self.db.get_ats_report("ats-db-test")
        self.assertIsNotNone(ats)
        self.assertEqual(ats["score"], 92)

        # 3. Test Analysis Report Write/Read
        self.db.create_analysis_report(
            analysis_id="anl-db-test",
            document_id="doc-db-test",
            workspace_id=self.workspace_id,
            report_data=json.dumps({"parser": {}, "ats": {}})
        )
        anl = self.db.get_analysis_report("anl-db-test")
        self.assertIsNotNone(anl)

        # 4. Test Comparison History Write/Read
        self.db.create_comparison_history(
            comparison_id="cmp-db-test",
            workspace_id=self.workspace_id,
            document_ids="doc1,doc2",
            comparison_data=json.dumps({"delta": "none"})
        )
        cmp = self.db.get_comparison_history("cmp-db-test")
        self.assertIsNotNone(cmp)

    def test_e2e_resume_platform_workflow(self) -> None:
        """E2E test verifying API paths upload -> analyze -> match -> compare -> export report."""
        
        # Reset event cache
        self.caught_events.clear()

        # 1. Ingest via upload endpoint
        file_payload = {"file": ("resume.txt", BytesIO(self.mock_resume_text.encode("utf-8")), "text/plain")}
        res_upload = self.client.post(f"/resume/upload?workspace_id={self.workspace_id}", files=file_payload)
        self.assertEqual(res_upload.status_code, 200)
        doc_id = res_upload.json().get("document_id")
        self.assertIsNotNone(doc_id)
        
        # Verify event 'resume.uploaded'
        self.event_bus.dispatch_all()
        self.assertIn("resume.uploaded", self.caught_events)

        # 2. Run Analyze Endpoint
        res_analyze = self.client.post("/resume/analyze", json={
            "document_id": doc_id,
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_analyze.status_code, 200)
        report = res_analyze.json()
        self.assertIsNotNone(report.get("analysis_id"))
        self.assertEqual(report.get("report_data", {}).get("parser", {}).get("name"), "Jane Doe")

        # Verify event 'resume.analyzed'
        self.event_bus.dispatch_all()
        self.assertIn("resume.analyzed", self.caught_events)

        # 3. Match against Job Description
        res_match = self.client.post("/resume/match", json={
            "document_id": doc_id,
            "jd": self.mock_jd,
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_match.status_code, 200)
        match_info = res_match.json()
        self.assertGreater(match_info.get("matcher", {}).get("compatibility_score", 0), 0)

        # Verify event 'resume.matched'
        self.event_bus.dispatch_all()
        self.assertIn("resume.matched", self.caught_events)

        # 4. Compare Resumes versions
        res_compare = self.client.post("/resume/compare", json={
            "document_ids": [doc_id],
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_compare.status_code, 200)
        compare_info = res_compare.json()
        self.assertIsNotNone(compare_info.get("comparison_id"))

        # Verify event 'resume.compared'
        self.event_bus.dispatch_all()
        self.assertIn("resume.compared", self.caught_events)

        # 5. Export formatted report
        res_report = self.client.get(f"/resume/report/{doc_id}?workspace_id={self.workspace_id}")
        self.assertEqual(res_report.status_code, 200)
        report_data = res_report.json()
        self.assertIn("markdown", report_data)
        self.assertIn("pdf_data_model", report_data)

        # Verify event 'resume.report.generated'
        self.event_bus.dispatch_all()
        self.assertIn("resume.report.generated", self.caught_events)
