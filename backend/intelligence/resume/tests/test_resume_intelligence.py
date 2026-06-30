"""Comprehensive E2E and unit test suite for the Resume Intelligence module."""

import json
import unittest
from unittest.mock import MagicMock, patch
import uuid
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.api.sqlite_mock import DBStorage
from backend.intelligence.resume.models import ResumeData, CategorizedSkills, ATSResult, JDMatchResult, ResumeAnalysis, ResumeReport
from backend.intelligence.resume.parser import ResumeParser, extract_raw_text
from backend.intelligence.resume.skill_extractor import SkillExtractor
from backend.intelligence.resume.ats_engine import ATSEngine
from backend.intelligence.resume.jd_matcher import JDMatcher
from backend.intelligence.resume.analyzer import ResumeAnalyzer
from backend.intelligence.resume.services import ResumeService
from backend.intelligence.resume.agent import ResumeAgent
from backend.runtime.task import Task
from backend.interfaces.model import InferenceResponse


class TestResumeIntelligence(unittest.TestCase):
    """Verifies parsing, ATS analysis, skill taxonomy sorting, and API routes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
        cls.client.__enter__()
        cls.db = DBStorage()
        
        # Start ModelRegistry mocks to mock LLM responses for test deterministic stability
        cls.list_providers_patcher = patch("backend.interfaces.model.ModelRegistry.list_providers")
        cls.get_provider_patcher = patch("backend.interfaces.model.ModelRegistry.get_provider")
        
        cls.mock_list_providers = cls.list_providers_patcher.start()
        cls.mock_get_provider = cls.get_provider_patcher.start()
        
        cls.mock_list_providers.return_value = ["mock_ollama"]
        
        cls.mock_provider = MagicMock()
        cls.mock_get_provider.return_value = cls.mock_provider
        
        # Set up mock response template
        cls.mock_llm_data = {
            "personal_info": {
                "full_name": "JOHN DOE",
                "email": "john.doe@example.com",
                "phone": "555-0199",
                "linkedin": "linkedin.com/in/johndoe",
                "github": "github.com/johndoe",
                "portfolio": "portfolio.com",
                "location": "Stanford"
            },
            "education": [
                {
                    "institution": "Stanford University",
                    "degree": "M.S.",
                    "branch": "Computer Science",
                    "gpa_cgpa": "4.0",
                    "graduation_year": "2022"
                }
            ],
            "experience": [
                {
                    "company": "TechCorp",
                    "role": "Senior Backend Engineer",
                    "start_date": "2022",
                    "end_date": "Present",
                    "duration": "2 years",
                    "responsibilities": ["Led design and implementation of distributed catalog service."]
                }
            ],
            "projects": [
                {
                    "project_name": "NexusAI",
                    "description": "Intent routing framework",
                    "technologies": ["Python", "FastAPI"],
                    "github_url": "github.com/johndoe/nexus",
                    "live_url": "nexus.example.com"
                }
            ],
            "skills": {
                "programming_languages": ["Python", "Go"],
                "frameworks": ["FastAPI"],
                "databases": ["PostgreSQL"],
                "cloud": ["AWS"],
                "ai_ml": ["LangChain"],
                "devops": ["Docker", "Kubernetes"],
                "tools": ["Git"],
                "soft_skills": []
            },
            "certifications": []
        }
        
        # Also mock general analysis SWOT response
        cls.mock_swot_data = {
            "strengths": ["Strong backend engineering experience with Python and Go", "Stanford MS graduate"],
            "weaknesses": ["Limited frontend development experience listed"],
            "improvement_suggestions": ["Add frontend projects to showcase full-stack capabilities"],
            "career_readiness": "Senior Backend Engineer",
            "interview_preparation_tips": ["Prepare for system design questions on distributed catalogs"]
        }
        
        # Also mock ATS analysis response
        cls.mock_ats_data = {
            "score": 85.0,
            "completeness_score": 90.0,
            "formatting_score": 95.0,
            "keyword_density_score": 80.0,
            "verb_metric_score": 85.0,
            "quantification_score": 90.0,
            "missing_keywords": ["Kubernetes"],
            "action_verbs_found": ["Led", "Built"],
            "missing_sections": [],
            "readability_level": "Standard"
        }
        
        # Also mock JD Match response
        cls.mock_match_data = {
            "match_percentage": 90.0,
            "matching_skills": ["Python", "FastAPI"],
            "missing_skills": ["AWS"],
            "missing_keywords": ["AWS"],
            "gap_analysis": "Missing direct AWS project execution",
            "recommendations": ["Add more cloud deployment details"],
            "section_specific_feedback": {}
        }
        
        # Define side_effect to dynamically return matching JSON schema for query type
        def mock_generate(req):
            prompt = req.prompt.lower()
            if "resume_general_analysis" in prompt:
                content_json = cls.mock_swot_data
            elif "resume_ats_analysis" in prompt:
                content_json = cls.mock_ats_data
            elif "resume_jd_matcher" in prompt:
                content_json = cls.mock_match_data
            elif "resume_skill_categorizer" in prompt:
                content_json = cls.mock_llm_data["skills"]
            else:
                content_json = cls.mock_llm_data
                
            return InferenceResponse(
                request_id=str(uuid.uuid4()),
                content=json.dumps(content_json),
                finish_reason="stop",
                token_usage={"prompt_tokens": 100, "completion_tokens": 100},
                latency=0.05,
                provider="ollama",
                model="mock",
                metadata={}
            )
            
        cls.mock_provider.generate.side_effect = mock_generate

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.__exit__(None, None, None)
        cls.list_providers_patcher.stop()
        cls.get_provider_patcher.stop()

    def setUp(self) -> None:
        import uuid
        self.workspace_id = f"test-ws-resume-{uuid.uuid4().hex[:8]}"
        # Seed test workspace
        try:
            self.db.create_workspace(self.workspace_id, "Test Resume Workspace", "admin")
        except Exception:
            pass

        self.resume_text = (
            "JOHN DOE\n"
            "Email: john.doe@example.com | Phone: 555-0199\n"
            "Links: github.com/johndoe, linkedin.com/in/johndoe\n\n"
            "EDUCATION\n"
            "M.S. in Computer Science - Stanford University, 2022\n\n"
            "EXPERIENCE\n"
            "Senior Backend Engineer at TechCorp (2022 - Present)\n"
            "- Led design and implementation of distributed catalog service scaling to 10M requests per day.\n"
            "- Built robust high-performance endpoints in Python using FastAPI, Docker, and PostgreSQL.\n\n"
            "PROJECTS\n"
            "NexusAI - Intent routing framework using local LLM orchestration.\n\n"
            "SKILLS\n"
            "Python, Go, FastAPI, PostgreSQL, AWS, Docker, Kubernetes, LangChain"
        )

    def test_plain_text_extraction(self) -> None:
        """Verifies text extraction parses plain text cleanly."""
        text = extract_raw_text(self.resume_text.encode("utf-8"), "resume.txt")
        self.assertIn("JOHN DOE", text)
        self.assertIn("Stanford", text)

    def test_parser_service(self) -> None:
        """Verifies parser extracts contact, education, and skills data."""
        parser = ResumeParser()
        data = parser.parse(self.resume_text.encode("utf-8"), "resume.txt")
        self.assertIsInstance(data, ResumeData)
        # Should populate fallback schema or extract details correctly
        self.assertIsNotNone(data.contact_info)
        self.assertGreater(len(data.skills), 0)

    def test_skill_extractor(self) -> None:
        """Verifies categorizer structures raw skills into tech categories."""
        parser = ResumeParser()
        data = parser.parse(self.resume_text.encode("utf-8"), "resume.txt")
        
        extractor = SkillExtractor()
        cat_skills = extractor.extract_and_categorize(data)
        self.assertIsInstance(cat_skills, CategorizedSkills)

    def test_ats_analyzer(self) -> None:
        """Verifies ATS scores and checks sections completeness."""
        parser = ResumeParser()
        data = parser.parse(self.resume_text.encode("utf-8"), "resume.txt")
        
        engine = ATSEngine()
        ats_res = engine.analyze_ats(data, self.resume_text)
        self.assertIsInstance(ats_res, ATSResult)
        self.assertTrue(0 <= ats_res.score <= 100)

    def test_jd_matcher(self) -> None:
        """Verifies job matching evaluates match percentage and skill gaps."""
        parser = ResumeParser()
        data = parser.parse(self.resume_text.encode("utf-8"), "resume.txt")
        
        jd = "Looking for a Senior Backend Python Developer with FastAPI, Docker, and Kubernetes skills."
        matcher = JDMatcher()
        match_res = matcher.match(data, self.resume_text, jd)
        self.assertIsInstance(match_res, JDMatchResult)
        self.assertTrue(0 <= match_res.match_percentage <= 100)

    def test_resume_analyzer(self) -> None:
        """Verifies general SWOT analysis generation."""
        parser = ResumeParser()
        data = parser.parse(self.resume_text.encode("utf-8"), "resume.txt")
        
        analyzer = ResumeAnalyzer()
        swot = analyzer.analyze(data, self.resume_text)
        self.assertIsInstance(swot, ResumeAnalysis)
        self.assertGreater(len(swot.strengths), 0)

    def test_agent_execution_parse(self) -> None:
        """Verifies ResumeAgent coordinates parse requests."""
        agent = ResumeAgent()
        agent.initialize()
        
        task = Task(
            description="Parse resume",
            metadata={
                "action": "parse",
                "contents": self.resume_text.encode("utf-8"),
                "filename": "resume.txt"
            }
        )
        res = agent.execute(task)
        self.assertIsInstance(res, ResumeData)

    def test_api_endpoints_workflow(self) -> None:
        """E2E verification of upload, analyze, jd-match, and report API endpoints."""
        # 1. POST /resume/upload
        files = {"file": ("resume.txt", self.resume_text.encode("utf-8"), "text/plain")}
        res = self.client.post(f"/resume/upload?workspace_id={self.workspace_id}", files=files)
        if res.status_code != 200:
            print("E2E_UPLOAD_FAIL_RESPONSE:", res.text)
        self.assertEqual(res.status_code, 200)
        
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("document_id", data)
        self.assertIn("resume_data", data)
        doc_id = data["document_id"]

        # 2. POST /resume/analyze
        res_anl = self.client.post("/resume/analyze", json={
            "document_id": doc_id,
            "workspace_id": self.workspace_id
        })
        if res_anl.status_code != 200:
            print("ANALYZE_FAIL_RESPONSE:", res_anl.text)
        self.assertEqual(res_anl.status_code, 200)
        
        anl_data = res_anl.json()
        self.assertIn("report_id", anl_data)
        self.assertIn("ats_analysis", anl_data)
        self.assertIn("general_analysis", anl_data)
        report_id = anl_data["report_id"]

        # 3. POST /resume/jd-match
        res_match = self.client.post("/resume/jd-match", json={
            "document_id": doc_id,
            "workspace_id": self.workspace_id,
            "jd": "We want a Senior Python developer who knows FastAPI and AWS cloud."
        })
        self.assertEqual(res_match.status_code, 200)
        
        match_data = res_match.json()
        self.assertIn("overall_score", match_data)
        self.assertIn("missing_skills", match_data)
        self.assertIn("matching_skills", match_data)
        self.assertIn("gap_analysis", match_data)

        # 4. GET /resume/report/{id}
        res_rep = self.client.get(f"/resume/report/{report_id}?workspace_id={self.workspace_id}")
        self.assertEqual(res_rep.status_code, 200)
        
        rep_data = res_rep.json()
        self.assertEqual(rep_data["report_id"], report_id)
        self.assertIn("categorized_skills", rep_data)
