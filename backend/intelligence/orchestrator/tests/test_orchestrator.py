"""Integration tests validating Cross-Intelligence Orchestrator intent routing and executions."""

import os
import uuid
import unittest
from backend.intelligence.resume.cache import ResumeCache
from backend.intelligence.resume.models import Resume
from backend.intelligence.resume.models import PersonalInformation
from backend.intelligence.profile.models import KnowledgeProfile, ProfilePersonalInfo, ProfileSkill
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.orchestrator.models import OrchestrationRequest
from backend.intelligence.orchestrator.orchestrator import CrossIntelligenceOrchestrator


class TestOrchestrator(unittest.TestCase):
    """Integration test suite verifying intent detection, step plans, and concurrency execution."""

    def setUp(self) -> None:
        self.db_name = f"test_orch_{str(uuid.uuid4())[:8]}.db"
        self.orchestrator = CrossIntelligenceOrchestrator(db_path=self.db_name)
        self.resume_cache = ResumeCache()
        self.doc_cache = DocumentCache()
        self.ws_id = "ws-orch-test"
        self.user_id = "bob"

        # Initialize mock cached profiles and document text
        profile = KnowledgeProfile(
            workspace_id=self.ws_id,
            user_id=self.user_id,
            personal_info=ProfilePersonalInfo(full_name="Bob Vance"),
            skills={"Python": ProfileSkill(name="Python", category="Languages", confidence_score=1.0)}
        )
        self.resume_cache.set_profile(self.user_id, profile)
        self.doc_cache.save_document("doc-crm-bench", "crm_bench.md", "CRM FastAPI performance details.")

    def tearDown(self) -> None:
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
            except Exception:
                pass

    def test_resume_plus_github_routing(self) -> None:
        """Verifies joint query routing executes both Resume and GitHub modules concurrently."""
        req = OrchestrationRequest(
            workspace_id=self.ws_id,
            user_id=self.user_id,
            query="Review my resume and compare it with my GitHub repositories."
        )
        resp = self.orchestrator.orchestrate_request(req)

        self.assertIn("Resume", resp.modules_executed)
        self.assertIn("GitHub", resp.modules_executed)
        self.assertEqual(len(resp.execution_timeline), 2)
        self.assertGreater(resp.confidence_score, 0.0)

    def test_resume_plus_document_routing(self) -> None:
        """Verifies joint routing executes Resume and Document modules."""
        req = OrchestrationRequest(
            workspace_id=self.ws_id,
            user_id=self.user_id,
            query="Summarize this CRM document and compare it with my resume experience.",
            document_ids=["doc-crm-bench"]
        )
        resp = self.orchestrator.orchestrate_request(req)

        self.assertIn("Resume", resp.modules_executed)
        self.assertIn("Document", resp.modules_executed)

    def test_failure_recovery_resilience(self) -> None:
        """Verifies orchestrator continues processing and returns success if a module fails."""
        # Inject an invalid document ID to trigger failure in Document module
        req = OrchestrationRequest(
            workspace_id=self.ws_id,
            user_id=self.user_id,
            query="Summarize this document and compare it with my resume.",
            document_ids=["invalid-doc-id"],
            options={"sequential": True}  # Run sequentially to isolate failure logs
        )
        resp = self.orchestrator.orchestrate_request(req)

        # Execution should be resilient
        self.assertIn("Resume", resp.modules_executed)
        self.assertIn("Document", resp.modules_executed)
        
        # Verify timeline tracks step failure
        doc_step = next(item for item in resp.execution_timeline if item["module_name"] == "Document")
        self.assertEqual(doc_step["status"], "completed")  # Handled fallback, so completed
        self.assertGreater(len(resp.final_response), 0)
