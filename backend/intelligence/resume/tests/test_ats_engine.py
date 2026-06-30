"""Unit tests for ATS Scoring Engine covering various candidate profiles and quality gaps."""

import unittest
from typing import List
from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill,
    CertificationEntry,
    SocialLink,
    VolunteerExperience,
    CustomSection,
    Award,
    Language,
    Publication,
    ResumeData,
    ContactInfo,
    EducationInfo,
    WorkExperience,
    ProjectInfo,
    CertificationInfo,
    ATSResult
)
from backend.intelligence.resume.ats_engine import ATSEngine
from backend.runtime.event import Event, EventType, EventBus


class TestATSEngine(unittest.TestCase):
    """Verifies ATS score calculations, feedback compile, and category weights."""

    def setUp(self) -> None:
        self.engine = ATSEngine()
        self.event_bus = EventBus()
        self.events_fired = []
        self.event_bus.subscribe("*", self.catch_event)

    def tearDown(self) -> None:
        self.event_bus.unsubscribe("*", self.catch_event)

    def catch_event(self, event: Event) -> None:
        self.events_fired.append(event)

    def _create_base_resume(self) -> Resume:
        """Helper to create a minimal valid Resume."""
        return Resume(
            personal_info=PersonalInformation(
                full_name="Base Candidate",
                email="candidate@base.com",
                phone="555-0100",
                location="San Francisco, CA",
                address="123 Base St",
                linkedin="https://linkedin.com/in/base",
                github="https://github.com/base",
                portfolio="https://base.dev",
                social_links=[
                    SocialLink(platform="LinkedIn", url="https://linkedin.com/in/base"),
                    SocialLink(platform="GitHub", url="https://github.com/base")
                ]
            ),
            education=[
                EducationEntry(
                    institution="Stanford University",
                    degree="Bachelor of Science",
                    branch="Computer Science",
                    graduation_year="2022",
                    start_year="2018",
                    end_year="2022",
                    gpa_cgpa="3.8",
                    description="Focused on systems programming."
                )
            ],
            experience=[
                ExperienceEntry(
                    company="TechCorp",
                    role="Software Engineer",
                    start_date="2022-06",
                    end_date="2024-06",
                    duration="2 years",
                    responsibilities=["Developed backend microservices using Python and FastAPI.", "Optimized SQL queries reducing response latency by 30%."],
                    achievements=["Successfully launched new check-out checkout scaling to 1M daily hits."],
                    location="SF",
                    technologies_used=["Python", "FastAPI", "PostgreSQL"]
                )
            ],
            projects=[
                ProjectEntry(
                    project_name="DataSync",
                    name="DataSync",
                    description="Designed and built a real-time data sync service orchestrating Kafka and Redis.",
                    technologies=["Kafka", "Redis", "Python"],
                    github_url="https://github.com/base/datasync",
                    live_url="https://datasync.demo",
                    github_link="https://github.com/base/datasync",
                    live_demo="https://datasync.demo",
                    contributions=["Implemented consumer group routing and automated offset checkpoints."]
                )
            ],
            skills=[
                Skill(name="Python", category="Programming Languages", proficiency="Expert"),
                Skill(name="FastAPI", category="Frameworks", proficiency="Expert"),
                Skill(name="PostgreSQL", category="Databases", proficiency="Intermediate"),
                Skill(name="Git", category="Tools", proficiency="Expert")
            ],
            certifications=[
                CertificationEntry(
                    certification_name="AWS Certified Solutions Architect",
                    organization="Amazon Web Services",
                    year="2023"
                )
            ]
        )

    def test_excellent_resume(self) -> None:
        """Verifies high scoring on an exceptionally detailed and complete profile."""
        resume = self._create_base_resume()
        
        # Add high tenure, leadership verbs, quantified metrics, and emerging tech
        resume.experience = [
            ExperienceEntry(
                company="InnovateLLC",
                role="Senior Software Engineer",
                start_date="2020-01",
                end_date="2024-06",
                duration="4.5 years",
                responsibilities=[
                    "Spearheaded redesign of distributed indexing pipeline scaling to 10M records per day.",
                    "Led a sub-team of 4 engineers in adopting unified Docker and Kubernetes standards.",
                    "Architected high-throughput REST APIs using Go and FastAPI."
                ],
                achievements=[
                    "Improved overall system performance by 45% and reduced cloud spend by $50k annually."
                ],
                technologies_used=["Go", "FastAPI", "Kubernetes", "Docker"]
            ),
            ExperienceEntry(
                company="TechCorp",
                role="Software Engineer",
                start_date="2018-01",
                end_date="2019-12",
                duration="2 years",
                responsibilities=[
                    "Developed backend microservices using Python and Django.",
                    "Implemented CI/CD pipelines using GitHub Actions."
                ],
                achievements=[],
                technologies_used=["Python", "Django", "Git"]
            )
        ]
        
        # Add multiple projects with descriptions, links, and action verbs
        resume.projects = [
            ProjectEntry(
                project_name="Generative Assistant",
                name="Generative Assistant",
                description="Designed and automated an agentic workflow utilizing LangChain, Pinecone, and local LLMs.",
                technologies=["LangChain", "Pinecone", "Python"],
                github_link="https://github.com/base/genai",
                live_demo="https://genai.app",
                contributions=["Pioneered retrieval augmented generation search filters improving accuracy by 40%."]
            ),
            ProjectEntry(
                project_name="Distributed Catalog",
                name="Distributed Catalog",
                description="Built a distributed catalogue database system using Rust, Redis, and raft consensus protocol.",
                technologies=["Rust", "Redis"],
                github_link="https://github.com/base/dist-cat",
                live_demo="https://distcat.demo",
                contributions=["Streamlined synchronization consensus across cluster nodes."]
            ),
            ProjectEntry(
                project_name="Legacy Migrator",
                name="Legacy Migrator",
                description="Integrated legacy SOAP APIs into modern graphql endpoints.",
                technologies=["GraphQL", "Node.js"],
                github_link="https://github.com/base/migrator"
            )
        ]
        
        # Add diverse skills, including emerging technologies
        resume.skills.extend([
            Skill(name="Go", category="Programming Languages", proficiency="Advanced"),
            Skill(name="Docker", category="DevOps", proficiency="Expert"),
            Skill(name="Kubernetes", category="DevOps", proficiency="Advanced"),
            Skill(name="LangChain", category="LLM Frameworks", proficiency="Advanced"),
            Skill(name="Pinecone", category="Vector Databases", proficiency="Advanced"),
            Skill(name="Generative AI", category="Generative AI", proficiency="Advanced")
        ])

        report = self.engine.evaluate_resume(resume)
        
        self.assertGreaterEqual(report.overall_score, 85.0)
        self.assertTrue(any("Distributed indexing pipeline" in s or "Tenure" in s or "skills" in s for s in report.strengths))
        self.assertGreater(len(report.strengths), 0)

    def test_average_resume(self) -> None:
        """Verifies average resume scores on a standard profile without leadership or emerging tech."""
        resume = self._create_base_resume()
        
        # Remove location/address
        resume.personal_info.location = ""
        resume.personal_info.address = ""
        
        # Shorten experience bullet points and remove metrics
        resume.experience = [
            ExperienceEntry(
                company="TechCorp",
                role="Software Engineer",
                start_date="2023-01",
                end_date="2024-01",
                duration="1 year",
                responsibilities=[
                    "helped with backend development using python",
                    "assisted with bug fixing and running local unit tests"
                ]
            )
        ]
        
        # Limit projects count
        resume.projects = [
            ProjectEntry(
                project_name="DataSync",
                name="DataSync",
                description="Short project description.",
                technologies=["Python"]
            )
        ]
        
        # No certifications
        resume.certifications = []

        report = self.engine.evaluate_resume(resume)
        self.assertTrue(report.overall_score >= 40.0 and report.overall_score < 80.0)
        self.assertGreater(len(report.priority_improvements), 0)

    def test_poor_resume(self) -> None:
        """Verifies low scores on highly incomplete resumes."""
        resume = Resume(
            personal_info=PersonalInformation(full_name="Poor Candidate"),
            education=[],
            experience=[],
            projects=[],
            skills=[]
        )

        report = self.engine.evaluate_resume(resume)
        self.assertLess(report.overall_score, 45.0)
        self.assertTrue(any("Missing the following contact details" in s.reason for s in report.category_scores))

    def test_missing_sections(self) -> None:
        """Verifies that missing core sections yield low Section Completeness scores."""
        resume = self._create_base_resume()
        resume.projects = []
        resume.skills = []

        report = self.engine.evaluate_resume(resume)
        sec_cat = next(c for c in report.category_scores if c.name == "Section Completeness")
        self.assertLess(sec_cat.current_score, 80.0)
        self.assertTrue(any("Projects" in s or "Skills" in s for s in sec_cat.improvement_suggestions))

    def test_duplicate_skills(self) -> None:
        """Verifies skill diversity penalty handles duplicate inputs or lacks emerging tech."""
        resume = self._create_base_resume()
        # Ensure only basic skills, zero emerging tech
        resume.skills = [
            Skill(name="Python", category="Programming Languages"),
            Skill(name="Python", category="Programming Languages"),
            Skill(name="FastAPI", category="Frameworks"),
            Skill(name="FastAPI", category="Frameworks")
        ]

        report = self.engine.evaluate_resume(resume)
        skill_cat = next(c for c in report.category_scores if c.name == "Skill Diversity")
        self.assertLess(skill_cat.current_score, 80.0)

    def test_weak_projects(self) -> None:
        """Verifies penalty on short project descriptions or missing links/tech stacks."""
        resume = self._create_base_resume()
        resume.projects = [
            ProjectEntry(
                project_name="DataSync",
                name="DataSync",
                description="very short",
                technologies=[]
            )
        ]

        report = self.engine.evaluate_resume(resume)
        proj_cat = next(c for c in report.category_scores if c.name == "Project Quality")
        self.assertLess(proj_cat.current_score, 70.0)
        self.assertTrue(any("Specify the tech stack" in s or "detailed descriptions" in s for s in proj_cat.improvement_suggestions))

    def test_no_experience(self) -> None:
        """Verifies scoring behaviour for profiles with no professional work experience listing."""
        resume = self._create_base_resume()
        resume.experience = []

        report = self.engine.evaluate_resume(resume)
        exp_cat = next(c for c in report.category_scores if c.name == "Experience Quality")
        self.assertEqual(exp_cat.current_score, 50.0)
        self.assertIn("Add internships, freelance work", exp_cat.improvement_suggestions[0])

    def test_student_resume(self) -> None:
        """Verifies scoring of student profile with strong academic focus but empty tenure."""
        resume = self._create_base_resume()
        resume.experience = []
        resume.education = [
            EducationEntry(
                institution="MIT",
                degree="M.S. in Computer Science",
                branch="Artificial Intelligence",
                graduation_year="2024",
                gpa_cgpa="3.95"
            )
        ]

        report = self.engine.evaluate_resume(resume)
        edu_cat = next(c for c in report.category_scores if c.name == "Education Completeness")
        self.assertEqual(edu_cat.current_score, 100.0)

    def test_experienced_professional(self) -> None:
        """Verifies high career progression and tenure rewards for seasoned candidates."""
        resume = self._create_base_resume()
        resume.experience = [
            ExperienceEntry(
                company="Global Inc",
                role="Principal Architect",
                start_date="2020-01",
                end_date="2024-06",
                duration="4.5 years",
                responsibilities=["Led cloud migrations.", "Architected core ingestion engine."],
                achievements=["Quantified success: Optimized throughput by 50% using Kafka."]
            ),
            ExperienceEntry(
                company="StartupCo",
                role="Software Engineer",
                start_date="2015-01",
                end_date="2019-12",
                duration="5 years",
                responsibilities=["Developed web servers."]
            )
        ]

        report = self.engine.evaluate_resume(resume)
        exp_cat = next(c for c in report.category_scores if c.name == "Experience Quality")
        self.assertGreaterEqual(exp_cat.current_score, 80.0)
        self.assertTrue("years" in exp_cat.reason)

    def test_analyze_ats_compatibility(self) -> None:
        """Verifies backwards-compatible analyze_ats method works through new scoring engine."""
        from backend.intelligence.resume.models import ContactInfo, EducationInfo, WorkExperience, ProjectInfo
        
        legacy_data = ResumeData(
            contact_info=ContactInfo(
                name="John Legacy",
                email="john@legacy.com",
                phone="123456",
                links=["https://linkedin.com/in/john", "https://github.com/john"]
            ),
            education=[
                EducationInfo(
                    institution="Stanford",
                    degree="BS",
                    field_of_study="CS",
                    graduation_year="2020"
                )
            ],
            experience=[
                WorkExperience(
                    company="Legacy Corp",
                    role="Developer",
                    start_date="2020-01",
                    end_date="2023-01",
                    responsibilities=["Developed ingestion pipeline.", "Optimized DB queries."]
                )
            ],
            projects=[
                ProjectInfo(
                    project_name="Legacy Project",
                    description="A basic backup script.",
                    technologies=["Python"]
                )
            ],
            skills=["Python", "SQL"]
        )

        result = self.engine.analyze_ats(legacy_data, "John Legacy raw resume text")
        self.assertIsInstance(result, ATSResult)
        self.assertGreater(result.score, 0.0)
        self.assertNotIn("python", result.missing_keywords)
        self.assertIn("go", result.missing_keywords)
