"""Tests for the Resume Intelligence Platform.

Verifies all 10 analytical tools, service orchestrations, and API gateway routes.
"""

from io import BytesIO
import json
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.resume_service import ResumeOrchestrationService
from backend.tools.tool import ToolRegistry, ToolRequest, ToolResponse
import backend.tools.resume_tools

class TestResumePlatform(unittest.TestCase):
    """Test suite covering tools execution, workflow services, and REST routes."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.tool_registry = ToolRegistry()
        self.workspace_id = "ws-test-resume"
        self.user_id = "admin"

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

    def test_tools_registration(self) -> None:
        """Verifies all 10 tools are registered in the ToolRegistry on load."""
        expected_tools = [
            "resume_parser", "skills_extractor", "experience_analyzer", 
            "education_analyzer", "ats_scoring", "jd_matcher", 
            "skill_gap_analyzer", "resume_improvement", "resume_comparison", "pdf_generator"
        ]
        registered = [t.schema.tool_id for t in self.tool_registry.list_tools()]
        for t in expected_tools:
            self.assertIn(t, registered, f"Tool '{t}' is not registered in the ToolRegistry.")

    def test_individual_tools_execution(self) -> None:
        """Verifies each tool executes successfully with mock fallback data."""
        # 1. Resume Parser Tool
        parser = self.tool_registry.get_tool("resume_parser")
        res = parser.execute(ToolRequest("r-1", "resume_parser", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertEqual(res.output.get("name"), "Jane Doe")

        # 2. Skills Extraction Tool
        skills = self.tool_registry.get_tool("skills_extractor")
        res = skills.execute(ToolRequest("r-2", "skills_extractor", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertIn("Python", res.output.get("hard_skills", []))

        # 3. Experience Analyzer Tool
        exp = self.tool_registry.get_tool("experience_analyzer")
        res = exp.execute(ToolRequest("r-3", "experience_analyzer", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertGreater(res.output.get("total_years", 0), 0)

        # 4. Education Analyzer Tool
        edu = self.tool_registry.get_tool("education_analyzer")
        res = edu.execute(ToolRequest("r-4", "education_analyzer", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertEqual(res.output.get("graduation_status"), "Graduated")

        # 5. ATS Scoring Tool
        ats = self.tool_registry.get_tool("ats_scoring")
        res = ats.execute(ToolRequest("r-5", "ats_scoring", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertGreater(res.output.get("ats_score", 0), 50)

        # 6. Job Description Matcher Tool
        matcher = self.tool_registry.get_tool("jd_matcher")
        res = matcher.execute(ToolRequest("r-6", "jd_matcher", self.workspace_id, self.user_id, {"text": self.mock_resume_text, "jd": self.mock_jd}))
        self.assertTrue(res.success)
        self.assertGreater(res.output.get("match_percentage", 0), 0)

        # 7. Skill Gap Analyzer Tool
        gap = self.tool_registry.get_tool("skill_gap_analyzer")
        res = gap.execute(ToolRequest("r-7", "skill_gap_analyzer", self.workspace_id, self.user_id, {"text": self.mock_resume_text, "jd": self.mock_jd}))
        self.assertTrue(res.success)
        self.assertIn("Kubernetes", res.output.get("missing_skills", []))

        # 8. Resume Improvement Tool
        improvement = self.tool_registry.get_tool("resume_improvement")
        res = improvement.execute(ToolRequest("r-8", "resume_improvement", self.workspace_id, self.user_id, {"text": self.mock_resume_text}))
        self.assertTrue(res.success)
        self.assertGreater(len(res.output.get("active_verbs_to_include", [])), 0)

        # 9. Resume Comparison Tool
        compare = self.tool_registry.get_tool("resume_comparison")
        res = compare.execute(ToolRequest("r-9", "resume_comparison", self.workspace_id, self.user_id, {
            "resumes": [{"candidate_id": "c-1", "text": self.mock_resume_text}],
            "jd": self.mock_jd
        }))
        self.assertTrue(res.success)
        self.assertGreater(len(res.output.get("rankings", [])), 0)

        # 10. PDF Report Generator Tool
        pdf = self.tool_registry.get_tool("pdf_generator")
        res = pdf.execute(ToolRequest("r-10", "pdf_generator", self.workspace_id, self.user_id, {
            "report_data": {
                "parser": {"name": "Jane Doe"},
                "ats": {"ats_score": 85},
                "skills": {"hard_skills": ["Python"]},
                "improvement": {"formatting_suggestions": ["Single page layout."]}
            }
        }))
        self.assertTrue(res.success)
        self.assertIn("Resume Intelligence Analysis Report", res.output)

    def test_e2e_resume_api_workflow(self) -> None:
        """E2E test verifying document upload -> analyze -> match -> compare -> export report API lifecycle."""
        
        # 1. Upload Resume REST Endpoint
        file_payload = {"file": ("resume.txt", BytesIO(self.mock_resume_text.encode("utf-8")), "text/plain")}
        res_upload = self.client.post(f"/api/resumes/upload?workspace_id={self.workspace_id}", files=file_payload)
        self.assertEqual(res_upload.status_code, 200)
        doc_id = res_upload.json().get("document_id")
        self.assertIsNotNone(doc_id)

        # 2. Analyze Resume REST Endpoint
        res_analyze = self.client.post("/api/resumes/analyze", json={
            "document_id": doc_id,
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_analyze.status_code, 200)
        report_data = res_analyze.json()
        self.assertEqual(report_data.get("parser", {}).get("name"), "Jane Doe")
        self.assertGreater(report_data.get("ats", {}).get("ats_score", 0), 50)

        # 3. Match Resume against Job Description REST Endpoint
        res_match = self.client.post("/api/resumes/match", json={
            "document_id": doc_id,
            "jd": self.mock_jd,
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_match.status_code, 200)
        match_data = res_match.json()
        self.assertGreater(match_data.get("matcher", {}).get("match_percentage", 0), 0)
        self.assertIn("Kubernetes", match_data.get("gap_analysis", {}).get("missing_skills", []))

        # 4. Compare Resumes REST Endpoint
        res_compare = self.client.post("/api/resumes/compare", json={
            "document_ids": [doc_id],
            "workspace_id": self.workspace_id,
            "jd": self.mock_jd
        })
        self.assertEqual(res_compare.status_code, 200)
        compare_data = res_compare.json()
        self.assertGreater(len(compare_data.get("rankings", [])), 0)

        # 5. Export Analytical Report REST Endpoint
        res_export = self.client.post("/api/resumes/export", json={
            "document_id": doc_id,
            "workspace_id": self.workspace_id
        })
        self.assertEqual(res_export.status_code, 200)
        export_data = res_export.json()
        self.assertIn("Resume Intelligence Analysis Report", export_data.get("report_export", ""))
