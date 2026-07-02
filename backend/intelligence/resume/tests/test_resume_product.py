"""End-to-end integration tests for the Resume Intelligence Product module."""

import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.intelligence.router import router as gateway_router
from backend.intelligence.resume.api import router as product_router
from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.resume.module import ResumeModule


from unittest.mock import patch, MagicMock


class TestResumeProduct(unittest.TestCase):
    """Verifies student/pro uploads, JD match alignment, invalid inputs, and background job polling."""

    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(product_router)
        self.app.include_router(gateway_router)
        self.client = TestClient(self.app)

        # Register ResumeModule in core registry
        self.registry = IntelligenceRegistry()
        self.registry.register(ResumeModule())

        self.patchers = [
            patch("backend.intelligence.resume.parser.ModelRegistry"),
            patch("backend.intelligence.resume.jd_parser.run_resume_llm_query"),
            patch("backend.intelligence.resume.skill_extractor.run_resume_llm_query")
        ]
        self.mocks = [p.start() for p in self.patchers]

        # Set up controlled ModelRegistry mock for parser.py
        def _make_parser_mock_registry(raw_text_capture):
            """Returns a ModelRegistry mock whose provider.generate returns controlled JSON."""
            import json

            mock_registry = MagicMock()
            mock_provider = MagicMock()
            mock_state = MagicMock()
            mock_state.model = "phi3:mini"
            mock_provider.provider_state = mock_state
            mock_registry.return_value.list_providers.return_value = ["ollama"]
            mock_registry.return_value.get_provider.return_value = mock_provider

            def controlled_generate(inf_req):
                raw = inf_req.prompt or ""
                if "student" in raw.lower():
                    data = {
                        "personal_info": {"full_name": "Jane Student", "email": "jane@example.com", "phone": "555-1234"},
                        "education": [{"institution": "Stanford", "degree": "BS", "branch": "Computer Science", "gpa_cgpa": None, "graduation_year": "2024"}],
                        "experience": [],
                        "projects": [],
                        "skills": {"programming_languages": ["Python", "Java"], "frameworks": ["Django"], "databases": [], "cloud": [], "ai_ml": [], "devops": [], "tools": [], "soft_skills": []},
                        "certifications": []
                    }
                else:
                    # Professional resume: 3 years experience
                    data = {
                        "personal_info": {"full_name": "Alice Senior", "email": "alice@example.com", "phone": "555-5678"},
                        "education": [],
                        "experience": [{"company": "TechCorp", "role": "Senior AI Engineer", "start_date": "2021-01", "end_date": "2024-01", "duration": "3 years", "responsibilities": ["Built ML pipelines", "Deployed LLM agents"]}],
                        "projects": [],
                        "skills": {"programming_languages": ["Python", "Go"], "frameworks": ["FastAPI"], "databases": [], "cloud": [], "ai_ml": ["PyTorch", "LLM"], "devops": [], "tools": [], "soft_skills": []},
                        "certifications": []
                    }
                mock_result = MagicMock()
                mock_result.content = json.dumps(data)
                return mock_result

            mock_provider.generate.side_effect = controlled_generate
            return mock_registry

        # Apply the parser ModelRegistry mock
        self.mocks[0].side_effect = None
        self.mocks[0].__class__ = type(self.mocks[0])
        # Re-configure mock[0] (the patched ModelRegistry class) directly
        import json
        mock_provider = MagicMock()
        mock_state = MagicMock()
        mock_state.model = "phi3:mini"
        mock_provider.provider_state = mock_state
        self.mocks[0].return_value.list_providers.return_value = ["ollama"]
        self.mocks[0].return_value.get_provider.return_value = mock_provider

        def controlled_generate(inf_req):
            raw = (inf_req.prompt or "").lower()
            if "student" in raw:
                data = {
                    "personal_info": {"full_name": "Jane Student", "email": "jane@example.com", "phone": "555-1234"},
                    "education": [{"institution": "Stanford", "degree": "BS", "branch": "Computer Science", "gpa_cgpa": None, "graduation_year": "2024"}],
                    "experience": [],
                    "projects": [],
                    "skills": {"programming_languages": ["Python", "Java"], "frameworks": ["Django"], "databases": [], "cloud": [], "ai_ml": [], "devops": [], "tools": [], "soft_skills": []},
                    "certifications": []
                }
            else:
                data = {
                    "personal_info": {"full_name": "Alice Senior", "email": "alice@example.com", "phone": "555-5678"},
                    "education": [],
                    "experience": [{"company": "TechCorp", "role": "Senior AI Engineer", "start_date": "2021-01", "end_date": "2024-01", "duration": "3 years", "responsibilities": ["Built ML pipelines", "Deployed LLM agents"]}],
                    "projects": [],
                    "skills": {"programming_languages": ["Python", "Go"], "frameworks": ["FastAPI"], "databases": [], "cloud": [], "ai_ml": ["PyTorch", "LLM"], "devops": [], "tools": [], "soft_skills": []},
                    "certifications": []
                }
            mock_result = MagicMock()
            mock_result.content = json.dumps(data)
            return mock_result

        mock_provider.generate.side_effect = controlled_generate
        
        def mock_jd_query(query_type: str, raw_text: str, schema: dict) -> dict:
            if not raw_text or not raw_text.strip():
                raise Exception("Corrupted raw text input")
            return {
                "job_title": "AI Engineer",
                "company": "TechCorp",
                "experience_required": "3 years",
                "education_requirements": ["BS in Computer Science"],
                "required_skills": ["Python", "PyTorch"],
                "preferred_skills": [],
                "responsibilities": ["Deploy models"],
                "technologies": ["Python"],
                "certifications": [],
                "soft_skills": [],
                "location": "Remote",
                "employment_type": "Full-time"
            }

        def mock_skill_query(query_type: str, raw_text: str, schema: dict) -> dict:
            if not raw_text or not raw_text.strip():
                raise Exception("Corrupted raw text input")
            return {
                "technical_skills": ["Python", "FastAPI", "Java"],
                "soft_skills": [],
                "tools": ["Docker"]
            }

        # mocks[1] = jd_parser.run_resume_llm_query
        self.mocks[1].side_effect = mock_jd_query
        # mocks[2] = skill_extractor.run_resume_llm_query
        self.mocks[2].side_effect = mock_skill_query

    def tearDown(self) -> None:
        for p in self.patchers:
            p.stop()

    def test_student_resume(self) -> None:
        """Verifies parsing, readiness assessment, and skill grouping for student resumes."""
        files = {
            "file": (
                "student.txt", 
                b"Name: Jane Student\nSkills: Python, Java\nEducation: BS in Computer Science", 
                "text/plain"
            )
        }
        resp_upload = self.client.post("/resume/upload?workspace_id=ws-student", files=files)
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        resp_anal = self.client.post(
            "/resume/analyze", 
            json={"document_id": doc_id, "workspace_id": "ws-student"}
        )
        self.assertEqual(resp_anal.status_code, 200)
        report = resp_anal.json()

        self.assertEqual(report["career_readiness"], "Student Backend Engineer")
        self.assertIn("Python", report["skill_analysis"]["technical_skills"])

    def test_professional_resume(self) -> None:
        """Verifies analysis matching for experienced professional resume details."""
        files = {
            "file": (
                "pro.txt", 
                b"Name: Alice Senior\nSkills: Python, PyTorch, Go\nExperience: Senior AI Engineer (3 years)", 
                "text/plain"
            )
        }
        resp_upload = self.client.post("/resume/upload?workspace_id=ws-pro", files=files)
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        resp_anal = self.client.post(
            "/resume/analyze", 
            json={"document_id": doc_id, "workspace_id": "ws-pro"}
        )
        self.assertEqual(resp_anal.status_code, 200)
        report = resp_anal.json()

        self.assertEqual(report["career_readiness"], "Mid-Level AI Engineer")

    def test_resume_plus_jd(self) -> None:
        """Verifies job matching recommendations and compatibility scores updates."""
        files = {
            "file": (
                "candidate.txt", 
                b"Name: Bob Dev\nSkills: Python, Django, SQL", 
                "text/plain"
            )
        }
        resp_upload = self.client.post("/resume/upload?workspace_id=ws-jd", files=files)
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        resp_match = self.client.post(
            "/resume/jd-match", 
            json={
                "document_id": doc_id,
                "workspace_id": "ws-jd",
                "jd": "We seek a developer skilled in Python and Django."
            }
        )
        self.assertEqual(resp_match.status_code, 200)
        match_data = resp_match.json()

        self.assertTrue(match_data["overall_score"] > 0)
        self.assertIn("Python", match_data["matching_skills"])

    def test_invalid_resume(self) -> None:
        """Verifies failed text extractions result in error response statuses."""
        files = {"file": ("empty.txt", b"", "text/plain")}
        response = self.client.post("/resume/upload?workspace_id=ws-invalid", files=files)
        self.assertTrue(response.status_code in [422, 500])

    def test_large_resume_async(self) -> None:
        """Verifies large resume files prompt background job response and progress polls."""
        large_content = b"Name: Dave Big\nSkills: Python\n" + (b"Experience: Developer\n" * 500)
        files = {"file": ("large.txt", large_content, "text/plain")}
        resp_upload = self.client.post("/resume/upload?workspace_id=ws-large", files=files)
        self.assertEqual(resp_upload.status_code, 200)
        doc_id = resp_upload.json()["document_id"]

        resp_anal = self.client.post(
            "/resume/analyze", 
            json={"document_id": doc_id, "workspace_id": "ws-large"}
        )
        self.assertEqual(resp_anal.status_code, 200)
        job_data = resp_anal.json()

        self.assertIn("job_id", job_data)
        job_id = job_data["job_id"]
        self.assertEqual(job_data["status"], "processing")

        # Poll the status endpoint until completed
        for _ in range(50):
            time.sleep(0.1)
            resp_poll = self.client.get(f"/resume/report/{job_id}")
            self.assertEqual(resp_poll.status_code, 200)
            poll_data = resp_poll.json()
            if poll_data["status"] == "completed":
                # Check generated report
                report_id = poll_data["report_id"]
                resp_rep = self.client.get(f"/resume/report/{report_id}")
                self.assertEqual(resp_rep.status_code, 200)
                
                # Check PDF export
                resp_pdf = self.client.get(f"/resume/report/{report_id}?export=pdf")
                self.assertEqual(resp_pdf.status_code, 200)
                self.assertEqual(resp_pdf.headers["content-type"], "application/pdf")
                break
        else:
            self.fail("Async background job did not complete in time.")

    def test_concurrent_users(self) -> None:
        """Verifies multi-user concurrency on execution runs directly at service layer."""
        from backend.intelligence.resume.models import ContactInfo, ResumeData
        from backend.intelligence.resume.service import ResumeProductService
        svc = ResumeProductService()
        
        resume = ResumeData(
            contact_info=ContactInfo(name="Jane Student"),
            skills=["Python", "FastAPI"]
        )

        def run_analyze() -> str:
            rep = svc.analyze_resume_sync(
                resume=resume,
                workspace_id="ws-concurrent",
                user_id="user-concurrent"
            )
            return rep.report_id

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(run_analyze) for _ in range(4)]
            for f in futures:
                self.assertIsNotNone(f.result())
