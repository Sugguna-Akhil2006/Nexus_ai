"""Unit tests for the Resume Analysis Engine."""

import unittest
from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    Language,
    Publication
)
from backend.intelligence.resume.resume_analyzer import ResumeAnalysisEngine
from backend.runtime.event import Event, EventBus


class TestResumeAnalyzer(unittest.TestCase):
    """Verifies career stage, track classification, readiness scoring, and strength/weakness parsing."""

    def setUp(self) -> None:
        self.engine = ResumeAnalysisEngine()
        self.event_bus = EventBus()
        self.events_fired = []
        self.event_bus.subscribe("*", self.catch_event)

    def tearDown(self) -> None:
        self.event_bus.unsubscribe("*", self.catch_event)

    def catch_event(self, event: Event) -> None:
        self.events_fired.append(event)

    def _create_base_resume(self) -> Resume:
        """Helper to create a solid baseline candidate resume."""
        return Resume(
            personal_info=PersonalInformation(
                full_name="John Doe",
                email="john@doe.com",
                phone="123456",
                github="https://github.com/johndoe",
                portfolio="https://johndoe.com/portfolio"
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
                    company="TechCorp",
                    role="Software Engineer",
                    start_date="2022-06",
                    end_date="2024-06",
                    responsibilities=["Developed REST APIs using FastAPI.", "Quantified impact by reducing latency by 20%."]
                )
            ],
            projects=[
                ProjectEntry(
                    project_name="Web Project",
                    description="A web app with frontend and backend components.",
                    technologies=["Python", "FastAPI", "React"],
                    contributions=["Created APIs.", "Built UI components."]
                )
            ],
            skills=[
                Skill(name="Python", category="Programming Languages"),
                Skill(name="FastAPI", category="Frameworks"),
                Skill(name="React", category="Frontend"),
                Skill(name="PostgreSQL", category="Databases"),
                Skill(name="Docker", category="DevOps")
            ]
        )

    def test_student_resume(self) -> None:
        """Verifies Student stage classification when work experience is empty."""
        resume = self._create_base_resume()
        resume.experience = []
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("Student", report.career_stage)
        self.assertGreaterEqual(report.career_readiness.score, 0.0)

    def test_experienced_resume(self) -> None:
        """Verifies Mid-Level / Senior classification based on tenure years."""
        resume = self._create_base_resume()
        resume.experience = [
            ExperienceEntry(
                company="OldCorp",
                role="Senior Engineer",
                start_date="2018-01",
                end_date="2024-06",
                description="Led core infrastructure scaling.",
                responsibilities=["Spearheaded migration.", "Mentored 5 developers."]
            )
        ]
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("Senior", report.career_stage)
        self.assertGreaterEqual(report.career_readiness.score, 70.0)

    def test_weak_resume(self) -> None:
        """Verifies critical recommendations and low scores for deficient profiles."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Jane Deficient"),
            skills=[Skill(name="Python")]
        )
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertLess(report.career_readiness.score, 60.0)
        
        # Verify Critical recommendations are present
        crit_recs = [r for r in report.recommendations if r.priority == "Critical"]
        self.assertTrue(len(crit_recs) > 0)
        self.assertTrue(any("Missing GitHub" in w for w in report.weaknesses))

    def test_strong_resume(self) -> None:
        """Verifies high readiness scores and certified/leadership strengths."""
        resume = self._create_base_resume()
        resume.certifications = [
            CertificationEntry(certification_name="AWS Solutions Architect")
        ]
        resume.experience.append(
            ExperienceEntry(
                company="BigCo",
                role="Engineering Lead",
                start_date="2020-01",
                end_date="2022-05",
                responsibilities=["Led 10 engineers.", "Reduced cloud costs by 30%."]
            )
        )
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertGreaterEqual(report.career_readiness.score, 80.0)
        self.assertTrue(any("Leadership" in s for s in report.strengths))
        self.assertTrue(any("AWS Solutions Architect" in s for s in report.strengths))

    def test_research_resume(self) -> None:
        """Verifies Research Engineer role specialization when publications exist."""
        resume = self._create_base_resume()
        resume.publications = [
            Publication(title="A Study on Neural RAG Networks", publisher="IEEE")
        ]
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("Research Engineer", report.career_stage)

    def test_ai_resume(self) -> None:
        """Verifies AI Engineer role specialization based on skill keywords."""
        resume = self._create_base_resume()
        resume.skills.extend([
            Skill(name="PyTorch"),
            Skill(name="LLM"),
            Skill(name="Generative AI")
        ])
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("AI Engineer", report.career_stage)

    def test_backend_resume(self) -> None:
        """Verifies Backend Engineer specialization when only backend stack exists."""
        resume = self._create_base_resume()
        # Remove React frontend skill and project tech
        resume.skills = [s for s in resume.skills if s.name != "React"]
        resume.projects = [
            ProjectEntry(
                project_name="Backend Project",
                description="Backend service design.",
                technologies=["Python", "FastAPI"]
            )
        ]
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("Backend Engineer", report.career_stage)

    def test_frontend_resume(self) -> None:
        """Verifies Frontend Engineer specialization when only frontend stack exists."""
        resume = self._create_base_resume()
        # Remove Python/FastAPI/Postgres backend skills and project tech
        resume.skills = [
            Skill(name="React"),
            Skill(name="HTML"),
            Skill(name="CSS"),
            Skill(name="JavaScript")
        ]
        resume.projects = [
            ProjectEntry(
                project_name="Frontend UI",
                description="Frontend presentation layout.",
                technologies=["React", "HTML", "CSS"]
            )
        ]
        resume.experience = [
            ExperienceEntry(
                company="TechCorp",
                role="Frontend Developer",
                start_date="2022-06",
                end_date="2024-06",
                responsibilities=["Developed UI layouts using React.", "Optimized frontend components performance."]
            )
        ]
        
        report = self.engine.analyze_resume_canonical(resume)
        self.assertIn("Frontend Engineer", report.career_stage)

    def test_events_firing(self) -> None:
        """Verifies that resume.analysis.completed event is published on EventBus."""
        resume = self._create_base_resume()
        self.engine.analyze_resume_canonical(resume)
        
        # Dispatch and inspect events
        self.event_bus.dispatch_all()
        event_types = [e.payload.get("event") for e in self.events_fired if e.payload]
        self.assertIn("resume.analysis.completed", event_types)
