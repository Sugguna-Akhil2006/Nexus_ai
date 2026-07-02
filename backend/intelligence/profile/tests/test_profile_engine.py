"""Unit and integration tests for the Unified Knowledge Profile Engine."""

import unittest

from backend.intelligence.profile.models import (
    KnowledgeProfile,
    ProfilePersonalInfo,
    ProfileSkill,
    ProfileSource,
    ProfileProject,
    ProfileExperience,
    ProfileEducation
)
from backend.intelligence.profile.services import ProfileService
from backend.intelligence.profile.identity import IdentityResolver
from backend.intelligence.resume.models import (
    Resume,
    PersonalInformation,
    EducationEntry,
    ExperienceEntry,
    ProjectEntry,
    Skill
)


class TestProfileEngine(unittest.TestCase):
    """Verifies profile merging policies, deduplication rules, timeline merges, and search."""

    def setUp(self) -> None:
        self.service = ProfileService()
        self.identity_resolver = IdentityResolver()

        # Create empty profile baseline
        self.profile = KnowledgeProfile(
            workspace_id="ws-test",
            user_id="user-123",
            personal_info=ProfilePersonalInfo(full_name="Alice Smith")
        )

    def _create_test_resume(self) -> Resume:
        return Resume(
            personal_info=PersonalInformation(
                full_name="Alice Smith",
                email="alice@smith.com",
                phone="987654",
                github="github.com/alice"
            ),
            education=[
                EducationEntry(
                    institution="Stanford",
                    degree="BS",
                    branch="CS",
                    graduation_year="2021"
                )
            ],
            experience=[
                ExperienceEntry(
                    company="AppCorp",
                    role="Developer",
                    start_date="2021-06",
                    end_date="2023-06",
                    responsibilities=["Created REST backend APIs in Python.", "Saved 10% query speeds."]
                )
            ],
            projects=[
                ProjectEntry(
                    project_name="WebProject",
                    description="Full stack app.",
                    technologies=["Python", "React"]
                )
            ],
            skills=[
                Skill(name="Python", category="Languages"),
                Skill(name="FastAPI", category="Frameworks")
            ]
        )

    def test_resume_only_aggregation(self) -> None:
        """Verifies simple aggregation of Resume details."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        self.assertEqual(p.personal_info.email, "alice@smith.com")
        self.assertIn("Python", p.skills)
        self.assertEqual(len(p.experience), 1)
        self.assertEqual(len(p.education), 1)
        self.assertEqual(len(p.timeline), 3)  # Education, Experience, Project

    def test_resume_plus_github(self) -> None:
        """Verifies merging GitHub repositories and languages into the profile."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        # Merge GitHub data
        repos = [{"name": "fastapi-core", "stars": 12}]
        languages = ["Python", "JavaScript"]
        
        p = self.service.aggregate_github(p, repos, languages)

        self.assertIn("JavaScript", p.skills)
        self.assertEqual(len(p.repositories), 1)
        self.assertEqual(p.skills["Python"].sources, ["Resume", "GitHub"])

    def test_duplicate_skills_resolution(self) -> None:
        """Verifies duplicate skill names are merged and sources are combined."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        # Incoming skills with duplicate names but different categories
        skills_dict = {
            "Python": ProfileSkill(name="Python", category="Data Science", confidence_score=0.9, sources=["GitHub"])
        }
        incoming = KnowledgeProfile(
            workspace_id="ws-test",
            user_id="user-123",
            skills=skills_dict
        )

        p = self.service.merger.merge_profiles(p, incoming)

        # Assert Python is unified
        self.assertIn("Python", p.skills)
        self.assertEqual(p.skills["Python"].category, "Languages")  # Preferred base category
        self.assertEqual(p.skills["Python"].confidence_score, 1.0)  # Takes max
        self.assertEqual(set(p.skills["Python"].sources), {"Resume", "GitHub"})

    def test_timeline_merge(self) -> None:
        """Verifies education and experience events are sorted reverse-chronologically."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        # Timeline has 3 items. Check sorting.
        # Developer at AppCorp (end_date: 2023-06) should be first
        # Studied BS at Stanford (graduation_year: 2021) should be second
        self.assertEqual(p.timeline[0].event_type, "Experience")
        self.assertEqual(p.timeline[1].event_type, "Education")

    def test_identity_resolution(self) -> None:
        """Verifies name, email, and github details match resolution."""
        base = ProfilePersonalInfo(full_name="Alice Smith", email="alice@smith.com")
        incoming = ProfilePersonalInfo(full_name="Alice S.", github="github.com/alice")
        
        # Match by name mismatch but email mismatch
        self.assertFalse(self.identity_resolver.resolve_identity(base, incoming))

        incoming.email = "alice@smith.com"
        self.assertTrue(self.identity_resolver.resolve_identity(base, incoming))

    def test_knowledge_graph_integrity(self) -> None:
        """Verifies nodes connections for project technologies and skill taxonomy directories."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        graph = p.knowledge_graph

        # Assert project links technologies
        self.assertIn("project:WebProject", graph)
        self.assertIn("skill:Python", graph["project:WebProject"])

        # Assert skill links category
        self.assertIn("skill:Python", graph)
        self.assertIn("category:Languages", graph["skill:Python"])

    def test_profile_search(self) -> None:
        """Verifies natural language query filtering returns matched items."""
        resume = self._create_test_resume()
        p = self.service.aggregate_resume(self.profile, resume)

        # 1. Search backend projects
        res = self.service.search_profile(p, "What backend projects has this user built?")
        self.assertTrue(len(res["matched_projects"]) > 0)
        self.assertEqual(res["matched_projects"][0]["name"], "WebProject")

        # 2. Search AI experience
        res = self.service.search_profile(p, "What AI experience does this person have?")
        # None, since Alice has CS and WebProject Developer role
        self.assertEqual(len(res["matched_experience"]), 0)
