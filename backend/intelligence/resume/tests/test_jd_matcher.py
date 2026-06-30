"""Unit tests for Job Description Matching Engine."""

import unittest
from unittest.mock import patch, MagicMock
from typing import List

from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    JobDescription,
    JDMatchReport,
    JDMatchResult,
    ResumeData,
    ContactInfo,
    EducationInfo,
    WorkExperience,
    ProjectInfo,
    CertificationInfo
)
from backend.intelligence.resume.jd_matcher import JDMatcher
from backend.runtime.event import Event, EventType, EventBus


class TestJDMatcher(unittest.TestCase):
    """Verifies Job Description Parsing, normalization, matching scoring, and gap prioritizing."""

    def setUp(self) -> None:
        self.matcher = JDMatcher()
        self.event_bus = EventBus()
        self.events_fired = []
        self.event_bus.subscribe("*", self.catch_event)
        
        # Patch local LLM query runner
        self.llm_patcher = patch("backend.intelligence.resume.jd_parser.run_resume_llm_query")
        self.mock_llm_query = self.llm_patcher.start()
        
        # Set up dynamic mock return templates based on query text
        def mock_query_side_effect(template_id, query_text, schema):
            query_lower = str(query_text).lower()
            if "ai engineer" in query_lower:
                return {
                    "job_title": "AI Engineer",
                    "company": "TechCorp",
                    "experience_required": "3 years",
                    "education_requirements": ["BS or MS in Computer Science"],
                    "required_skills": ["Python", "PyTorch", "Generative AI"],
                    "preferred_skills": ["LangChain", "Pinecone"],
                    "responsibilities": ["Build LLM agents"],
                    "technologies": ["Python", "Pinecone"],
                    "certifications": ["AWS Certified Machine Learning"],
                    "soft_skills": ["communication"],
                    "location": "Remote",
                    "employment_type": "Full-time"
                }
            elif "full stack" in query_lower:
                return {
                    "job_title": "Full Stack Engineer",
                    "company": "WebCorp",
                    "experience_required": "5 years",
                    "education_requirements": ["BS in Computer Science"],
                    "required_skills": ["React", "Node.js", "JavaScript"],
                    "preferred_skills": ["Docker", "AWS"],
                    "responsibilities": ["Full stack web development"],
                    "technologies": ["React", "Node.js"],
                    "certifications": [],
                    "soft_skills": ["teamwork"],
                    "location": "Hybrid",
                    "employment_type": "Full-time"
                }
            elif "data scientist" in query_lower:
                return {
                    "job_title": "Data Scientist",
                    "company": "DataCorp",
                    "experience_required": "4 years",
                    "education_requirements": ["MS or PhD in Statistics"],
                    "required_skills": ["Python", "Statistics", "Machine Learning"],
                    "preferred_skills": ["SQL", "Tableau"],
                    "responsibilities": ["Train ML models"],
                    "technologies": ["Python", "SQL"],
                    "certifications": [],
                    "soft_skills": ["problem solving"],
                    "location": "NY",
                    "employment_type": "Full-time"
                }
            else:
                return {
                    "job_title": "Backend Engineer",
                    "company": "BaseCorp",
                    "experience_required": "2 years",
                    "education_requirements": ["Bachelor in Computer Science"],
                    "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                    "preferred_skills": ["Docker", "Git"],
                    "responsibilities": ["Build APIs"],
                    "technologies": ["Python", "FastAPI"],
                    "certifications": [],
                    "soft_skills": [],
                    "location": "SF",
                    "employment_type": "Full-time"
                }
                
        self.mock_llm_query.side_effect = mock_query_side_effect

    def tearDown(self) -> None:
        self.llm_patcher.stop()
        self.event_bus.unsubscribe("*", self.catch_event)

    def catch_event(self, event: Event) -> None:
        self.events_fired.append(event)

    def _create_candidate_resume(self) -> Resume:
        """Helper to create a solid backend candidate resume."""
        return Resume(
            personal_info=PersonalInformation(
                full_name="John Doe",
                email="john@doe.com",
                phone="123456",
                linkedin="https://linkedin.com/in/johndoe",
                github="https://github.com/johndoe"
            ),
            education=[
                EducationEntry(
                    institution="Stanford University",
                    degree="BS",
                    branch="Computer Science",
                    graduation_year="2022"
                )
            ],
            experience=[
                ExperienceEntry(
                    company="BaseCorp",
                    role="Software Engineer",
                    start_date="2022-06",
                    end_date="2024-06",
                    responsibilities=["Developed REST APIs in Python using FastAPI.", "Configured PostgreSQL databases."]
                )
            ],
            projects=[
                ProjectEntry(
                    project_name="Legacy Project",
                    description="A modern backend script built in Python using FastAPI.",
                    technologies=["Python", "FastAPI"]
                )
            ],
            skills=[
                Skill(name="Python", category="Programming Languages"),
                Skill(name="FastAPI", category="Frameworks"),
                Skill(name="PostgreSQL", category="Databases")
            ],
            certifications=[]
        )

    def test_excellent_match(self) -> None:
        """Verifies perfect suitability matches yield high overall scores."""
        resume = self._create_candidate_resume()
        
        # Test against standard Backend JD (which candidate fits perfectly)
        jd = self.matcher.parser.parse_jd("Job Description details for a Backend Engineer")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertGreaterEqual(report.overall_score, 80.0)
        self.assertTrue(any("go" in g.lower() or "docker" in g.lower() for g in report.gap_analysis))
        self.assertGreater(len(report.matching_skills), 0)

        # Check events
        self.event_bus.dispatch_all()
        event_types = [e.payload.get("event") for e in self.events_fired if e.payload]
        self.assertIn("resume.jd.parsed", event_types)
        self.assertIn("resume.jd.matched", event_types)

    def test_average_match(self) -> None:
        """Verifies candidate with partial fit yields average match scores."""
        resume = self._create_candidate_resume()
        
        # Candidate has basic Python but lacks PyTorch and AWS Certified Machine Learning
        jd = self.matcher.parser.parse_jd("Looking for an AI Engineer with PyTorch experience")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertTrue(report.overall_score >= 40.0 and report.overall_score < 80.0)
        self.assertTrue(any("pytorch" in g.lower() for g in report.gap_analysis))

    def test_poor_match(self) -> None:
        """Verifies candidate with zero overlapping stack yields poor match scores."""
        resume = self._create_candidate_resume()
        
        # Full stack JD requires React, Node.js, JavaScript which candidate lacks
        jd = self.matcher.parser.parse_jd("Job Description details for a Full Stack position")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertLess(report.overall_score, 50.0)

    def test_student_resume(self) -> None:
        """Verifies student match behavior (no work experience tenure)."""
        resume = self._create_candidate_resume()
        resume.experience = []
        
        jd = self.matcher.parser.parse_jd("Job Description details for a Backend Engineer")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        # Experience match score should reflect missing tenure
        exp_score = next(c for c in report.category_scores if c.category_name == "Experience")
        self.assertLess(exp_score.score, 100.0)

    def test_experienced_professional(self) -> None:
        """Verifies long tenure professional fully satisfies experience target thresholds."""
        resume = self._create_candidate_resume()
        resume.experience = [
            ExperienceEntry(
                company="TechGiant",
                role="Senior Engineer",
                start_date="2015-01",
                end_date="2024-06",
                responsibilities=["Led core systems design."]
            )
        ]
        
        jd = self.matcher.parser.parse_jd("Job Description details for an AI Engineer requiring 3 years")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        exp_score = next(c for c in report.category_scores if c.category_name == "Experience")
        self.assertEqual(exp_score.score, 100.0)

    def test_ai_engineer_jd(self) -> None:
        """Verifies matching against specialized AI Engineer JD."""
        resume = self._create_candidate_resume()
        resume.skills.extend([
            Skill(name="PyTorch", category="AI/ML Skills"),
            Skill(name="Generative AI", category="AI/ML Skills"),
            Skill(name="Pinecone", category="Vector Databases")
        ])
        
        jd = self.matcher.parser.parse_jd("Job Description details for an AI Engineer")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertGreaterEqual(report.overall_score, 75.0)

    def test_full_stack_jd(self) -> None:
        """Verifies matching against specialized Full Stack JD."""
        resume = self._create_candidate_resume()
        resume.skills.extend([
            Skill(name="React", category="Frontend"),
            Skill(name="Node.js", category="Backend")
        ])
        
        jd = self.matcher.parser.parse_jd("Job Description details for a Full Stack Engineer")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertGreaterEqual(report.overall_score, 50.0)

    def test_data_scientist_jd(self) -> None:
        """Verifies matching against specialized Data Scientist JD."""
        resume = self._create_candidate_resume()
        resume.education = [
            EducationEntry(
                institution="Columbia",
                degree="MS",
                branch="Statistics",
                graduation_year="2020"
            )
        ]
        resume.skills.extend([
            Skill(name="Statistics", category="Data Science"),
            Skill(name="Machine Learning", category="Data Science")
        ])
        
        jd = self.matcher.parser.parse_jd("Job Description details for a Data Scientist")
        report = self.matcher.match_resume_to_jd(resume, jd)
        
        self.assertGreaterEqual(report.overall_score, 70.0)

    def test_backwards_compatibility_match(self) -> None:
        """Verifies legacy match method produces a valid JDMatchResult."""
        legacy_data = ResumeData(
            contact_info=ContactInfo(name="John Legacy", email="john@legacy.com"),
            education=[EducationInfo(institution="Stanford", degree="BS", field_of_study="CS")],
            experience=[WorkExperience(company="BaseCorp", role="Developer", start_date="2022-06", end_date="2024-06")],
            projects=[ProjectInfo(project_name="Legacy Project", description="A basic backup script", technologies=["Python"])],
            skills=["Python", "FastAPI"]
        )
        
        result = self.matcher.match(legacy_data, "John Legacy raw text", "Looking for a Backend Engineer")
        self.assertIsInstance(result, JDMatchResult)
        self.assertGreater(result.match_percentage, 0.0)
        self.assertIn("Programming Languages", result.section_specific_feedback)
