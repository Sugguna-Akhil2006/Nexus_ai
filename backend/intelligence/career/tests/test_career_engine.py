"""Comprehensive tests for the Career Intelligence Engine."""

import time
import unittest

from backend.intelligence.career.models import (
    CareerAnalysisRequest,
    CareerLevel,
    CareerProfile,
    RecommendationType,
)
from backend.intelligence.career.career_agent import CareerAgent
from backend.intelligence.career.career_gap_analyzer import CareerGapAnalyzer
from backend.intelligence.career.job_matcher import JobMatcher
from backend.intelligence.career.roadmap_generator import RoadmapGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent() -> CareerAgent:
    return CareerAgent()


def _student_profile() -> CareerProfile:
    return CareerProfile(
        name="Alice Student",
        current_role="CS Student",
        years_experience=0.5,
        skills=["Python", "HTML", "CSS"],
        github_languages=["Python"],
        github_projects=["personal-website"],
        certifications=[],
        workspace_id="ws-student",
    )


def _senior_profile() -> CareerProfile:
    return CareerProfile(
        name="Bob Senior",
        current_role="Senior Software Engineer",
        years_experience=7.0,
        skills=["Python", "FastAPI", "Docker", "Kubernetes", "SQL", "AWS", "TypeScript", "React"],
        github_languages=["Python", "TypeScript", "Rust"],
        github_projects=["microservice-platform", "k8s-operator", "rust-cli"],
        certifications=["AWS Certified Developer"],
        workspace_id="ws-senior",
    )


def _github_only_profile() -> CareerProfile:
    return CareerProfile(
        name="Carol GitHub",
        current_role="",
        years_experience=2.0,
        skills=[],
        github_languages=["JavaScript", "TypeScript", "Python"],
        github_projects=["open-source-lib", "cli-tool"],
        certifications=[],
        workspace_id="ws-github",
    )


def _target_backend_skills():
    return ["Python", "FastAPI", "Docker", "SQL", "Redis", "Kubernetes", "AWS"]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestStudentResume(unittest.TestCase):
    """Student with minimal skills should have large gap and detailed roadmap."""

    def setUp(self):
        self.agent = _make_agent()
        self.profile = _student_profile()

    def test_analysis_completes(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-student",
            profile=self.profile,
            target_role="Backend Developer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        self.assertIsNotNone(report)
        self.assertEqual(report.career_level, CareerLevel.STUDENT)

    def test_large_skill_gap(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-student",
            profile=self.profile,
            target_role="Backend Developer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        # Student has python but misses docker, sql, redis, kubernetes, aws
        self.assertGreater(len(report.skill_gaps), 2)

    def test_roadmap_has_steps(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-student",
            profile=self.profile,
            target_role="Backend Developer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        self.assertIsNotNone(report.roadmap)
        self.assertGreater(len(report.roadmap.steps), 0)

    def test_recommendations_generated(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-student",
            profile=self.profile,
            target_role="Backend Developer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        self.assertGreater(len(report.recommendations), 0)
        types = {r.rec_type for r in report.recommendations}
        self.assertIn(RecommendationType.LEARNING, types)


class TestExperiencedProfessional(unittest.TestCase):
    """Senior engineer should have high match %, few gaps, and SENIOR level."""

    def setUp(self):
        self.agent = _make_agent()
        self.profile = _senior_profile()

    def test_career_level_senior(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-senior",
            profile=self.profile,
            target_role="Staff Engineer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        self.assertEqual(report.career_level, CareerLevel.SENIOR)

    def test_few_or_no_gaps(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-senior",
            profile=self.profile,
            target_role="Staff Engineer",
            target_skills=["Python", "Docker", "Kubernetes", "AWS"],
        )
        report = self.agent.analyze(req)
        # Senior covers all four target skills
        self.assertEqual(len(report.skill_gaps), 0)

    def test_strengths_populated(self):
        req = CareerAnalysisRequest(
            workspace_id="ws-senior",
            profile=self.profile,
            target_role="Staff Engineer",
            target_skills=_target_backend_skills(),
        )
        report = self.agent.analyze(req)
        self.assertGreater(len(report.strengths), 0)


class TestGitHubOnlyProfile(unittest.TestCase):
    """Profile with no resume skills uses GitHub languages for gap analysis."""

    def test_github_languages_count_as_skills(self):
        agent = _make_agent()
        profile = _github_only_profile()
        req = CareerAnalysisRequest(
            workspace_id="ws-github",
            profile=profile,
            target_role="Frontend Developer",
            target_skills=["JavaScript", "TypeScript", "React", "CSS"],
        )
        report = agent.analyze(req)
        # JavaScript and TypeScript should be matched from github_languages
        matched_skills = {g.skill.lower() for g in report.skill_gaps}
        self.assertNotIn("javascript", matched_skills)
        self.assertNotIn("typescript", matched_skills)

    def test_report_generated_without_resume(self):
        agent = _make_agent()
        profile = _github_only_profile()
        req = CareerAnalysisRequest(
            workspace_id="ws-github",
            profile=profile,
            target_role="Open Source Developer",
            target_skills=["Python", "TypeScript"],
        )
        report = agent.analyze(req)
        self.assertIsNotNone(report.report_id)


class TestResumeAndGitHub(unittest.TestCase):
    """Combined resume + GitHub should produce cross-correlated strengths."""

    def test_combined_skills_reduce_gaps(self):
        agent = _make_agent()
        profile = CareerProfile(
            name="Dave Full",
            current_role="Mid Engineer",
            years_experience=3.0,
            skills=["Python", "FastAPI", "SQL"],
            github_languages=["Python", "Docker"],
            workspace_id="ws-full",
        )
        req = CareerAnalysisRequest(
            workspace_id="ws-full",
            profile=profile,
            target_role="Backend Engineer",
            target_skills=["Python", "FastAPI", "Docker", "SQL", "Redis"],
        )
        report = agent.analyze(req)
        gap_skills = {g.skill.lower() for g in report.skill_gaps}
        # Docker should be covered by github_languages
        self.assertNotIn("docker", gap_skills)
        # Redis is missing
        self.assertIn("redis", gap_skills)


class TestResumeAndDocuments(unittest.TestCase):
    """Certification docs should reduce skill gaps."""

    def test_certifications_reduce_gaps(self):
        agent = _make_agent()
        profile = CareerProfile(
            name="Eve Certified",
            current_role="Cloud Engineer",
            years_experience=4.0,
            skills=["Python", "Terraform"],
            github_languages=["Python"],
            certifications=["AWS Certified Developer", "Docker Certified Associate"],
            document_topics=["cloud infrastructure", "container orchestration"],
            workspace_id="ws-certs",
        )
        req = CareerAnalysisRequest(
            workspace_id="ws-certs",
            profile=profile,
            target_role="DevOps Engineer",
            target_skills=["Python", "Docker", "AWS", "Terraform", "Kubernetes"],
        )
        report = agent.analyze(req)
        gap_skills = {g.skill.lower() for g in report.skill_gaps}
        # AWS is covered by certification
        self.assertNotIn("aws", gap_skills)


class TestLargePortfolio(unittest.TestCase):
    """20+ skills should process within performance budget."""

    def test_large_portfolio_performance(self):
        agent = _make_agent()
        large_skills = [
            "Python", "FastAPI", "Django", "Flask", "Docker", "Kubernetes",
            "AWS", "GCP", "Azure", "Terraform", "SQL", "PostgreSQL", "Redis",
            "Kafka", "RabbitMQ", "TypeScript", "React", "GraphQL", "Rust", "Go",
        ]
        profile = CareerProfile(
            name="Frank Large",
            current_role="Principal Engineer",
            years_experience=12.0,
            skills=large_skills,
            github_languages=["Python", "Go", "Rust", "TypeScript"],
            workspace_id="ws-large",
        )
        req = CareerAnalysisRequest(
            workspace_id="ws-large",
            profile=profile,
            target_role="Staff Engineer",
            target_skills=large_skills,
        )
        start = time.perf_counter()
        report = agent.analyze(req)
        duration = time.perf_counter() - start

        self.assertLess(duration, 2.0, "Large portfolio analysis exceeded 2-second budget.")
        self.assertEqual(len(report.skill_gaps), 0)
        self.assertEqual(report.career_level, CareerLevel.PRINCIPAL)


class TestJobMatching(unittest.TestCase):
    """Job matcher produces correct match % and improvement hints."""

    def test_full_match(self):
        matcher = JobMatcher()
        profile = _senior_profile()
        jd = "We need Python FastAPI Docker Kubernetes AWS TypeScript React SQL experience."
        result = matcher.match(profile, jd, job_title="Full Stack Engineer")
        self.assertGreater(result.skill_match_pct, 50.0)

    def test_partial_match_missing_skills_listed(self):
        matcher = JobMatcher()
        profile = _student_profile()
        jd = "Looking for Python FastAPI Docker Kubernetes AWS PostgreSQL Redis Kafka engineer."
        result = matcher.match(profile, jd)
        self.assertGreater(len(result.missing_skills), 0)
        self.assertGreater(len(result.resume_improvements), 0)

    def test_job_match_via_agent(self):
        agent = _make_agent()
        profile = _student_profile()
        jd = "Seeking Python developer with FastAPI Docker experience."
        result = agent.match_job(profile, jd, job_title="Python Developer")
        self.assertIsNotNone(result.match_id)


class TestRoadmapGeneration(unittest.TestCase):
    """Standalone roadmap generation via CareerAgent."""

    def test_roadmap_step_count_matches_gaps(self):
        agent = _make_agent()
        profile = _student_profile()
        target = ["Docker", "Kubernetes", "SQL", "Redis"]
        roadmap = agent.generate_roadmap(profile, target, target_role="DevOps Engineer")
        # Student has none of these → 4 gaps → 4 roadmap steps
        self.assertEqual(len(roadmap.steps), 4)

    def test_roadmap_total_weeks_positive(self):
        agent = _make_agent()
        profile = _student_profile()
        roadmap = agent.generate_roadmap(profile, ["Docker", "SQL"])
        self.assertGreater(roadmap.total_estimated_weeks, 0)

    def test_roadmap_target_role_propagated(self):
        agent = _make_agent()
        profile = _student_profile()
        roadmap = agent.generate_roadmap(profile, ["Docker"], target_role="Cloud Engineer")
        self.assertEqual(roadmap.target_role, "Cloud Engineer")


class TestReportRetrieval(unittest.TestCase):
    """Report persistence and retrieval."""

    def test_report_retrievable_by_id(self):
        agent = _make_agent()
        req = CareerAnalysisRequest(
            workspace_id="ws-ret",
            profile=_student_profile(),
            target_role="Developer",
            target_skills=["Docker"],
        )
        report = agent.analyze(req)
        retrieved = agent.get_report(report.report_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.report_id, report.report_id)

    def test_unknown_report_returns_none(self):
        agent = _make_agent()
        self.assertIsNone(agent.get_report("nonexistent-id"))


if __name__ == "__main__":
    unittest.main()
