"""Comprehensive tests for the Unified Professional Intelligence Engine."""

import time
import unittest

from backend.intelligence.professional.models import (
    EvidenceSource,
    ProfessionalAnalysisRequest,
    ProfessionalTier,
)
from backend.intelligence.professional.professional_agent import ProfessionalAgent


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_agent() -> ProfessionalAgent:
    return ProfessionalAgent()


def _resume_only_request() -> ProfessionalAnalysisRequest:
    return ProfessionalAnalysisRequest(
        workspace_id="ws-resume-only",
        resume_name="Alice Candidate",
        resume_current_role="Backend Developer",
        resume_years_experience=3.0,
        resume_skills=["Python", "FastAPI", "SQL"],
        resume_certifications=["AWS Practitioner"],
        target_role="Senior Backend Engineer",
        target_skills=["Python", "FastAPI", "Docker", "SQL", "Kubernetes"],
    )


def _github_only_request() -> ProfessionalAnalysisRequest:
    return ProfessionalAnalysisRequest(
        workspace_id="ws-github-only",
        github_username="bob_git",
        github_languages=["Python", "Go", "TypeScript"],
        github_projects=["fastapi-boilerplate", "go-cli", "react-dashboard"],
        target_role="Backend Developer",
        target_skills=["Python", "Go", "Docker"],
    )


def _resume_github_request() -> ProfessionalAnalysisRequest:
    return ProfessionalAnalysisRequest(
        workspace_id="ws-resume-github",
        resume_name="Carol Engineer",
        resume_current_role="Mid Backend Developer",
        resume_years_experience=4.0,
        resume_skills=["Python", "FastAPI", "Docker", "SQL"],
        github_username="carol_eng",
        github_languages=["Python", "SQL"],
        github_projects=["microservices-fastapi", "db-migration-tool"],
        target_role="Senior Backend Developer",
        target_skills=["Python", "FastAPI", "Docker", "SQL", "Redis"],
    )


def _resume_documents_request() -> ProfessionalAnalysisRequest:
    return ProfessionalAnalysisRequest(
        workspace_id="ws-resume-docs",
        resume_name="Dave Cloud",
        resume_current_role="Sysadmin",
        resume_years_experience=5.0,
        resume_skills=["Linux", "Bash", "Python"],
        resume_certifications=["CKA"],
        document_topics=["kubernetes administration", "container architecture"],
        target_role="DevOps Engineer",
        target_skills=["Linux", "Kubernetes", "Docker", "Python"],
    )


def _complete_portfolio_request() -> ProfessionalAnalysisRequest:
    return ProfessionalAnalysisRequest(
        workspace_id="ws-complete",
        resume_name="Eve Lead",
        resume_current_role="Senior DevOps Engineer",
        resume_years_experience=8.0,
        resume_skills=["Python", "Go", "Docker", "Kubernetes", "AWS", "Terraform"],
        github_username="eve_devops",
        github_languages=["Go", "Python", "HCL"],
        github_projects=["k8s-deployment-operator", "aws-infra-module", "go-metrics-lib"],
        resume_certifications=["CKAD", "AWS Developer Associate"],
        document_topics=["kubernetes clusters", "aws cloud design", "terraform workspace"],
        target_role="Principal Infrastructure Engineer",
        target_skills=["Go", "Kubernetes", "AWS", "Terraform", "Security"],
    )


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

class TestResumeOnly(unittest.TestCase):
    """Resume-only profiles are scored and verified with resume-only evidence."""

    def test_resume_only_scenarios(self):
        agent = _make_agent()
        req = _resume_only_request()

        # Generate report
        report = agent.analyze(req)
        self.assertIsNotNone(report)
        self.assertIsNotNone(report.professional_score)

        # Standalone score
        score = agent.score(req)
        self.assertIsNotNone(score)
        # Without github, github quality score component should be 0.0
        self.assertEqual(score.components.github_quality, 0.0)

        # Skill verification: all skills should have RESUME source and NOT be verified (needs 2+ sources)
        for skill_ev in report.verified_skills:
            self.assertIn(EvidenceSource.RESUME, skill_ev.sources)
            self.assertFalse(skill_ev.verified)
            self.assertEqual(skill_ev.confidence, 0.6)  # 1 * 0.40 + 0.20


class TestGitHubOnly(unittest.TestCase):
    """GitHub-only profiles are scored and verified with github-only evidence."""

    def test_github_only_scenarios(self):
        agent = _make_agent()
        req = _github_only_request()

        # Standalone score
        score = agent.score(req)
        self.assertIsNotNone(score)
        # Without resume, resume quality should be minimal or based purely on empty/zero inputs
        self.assertEqual(score.components.resume_quality, 0.0)

        # Report analysis
        report = agent.analyze(req)
        self.assertIsNotNone(report)
        # verified projects should be populated from github repos/projects
        self.assertEqual(len(report.verified_projects), 3)
        self.assertIn("fastapi-boilerplate", report.verified_projects)


class TestResumeGitHub(unittest.TestCase):
    """Combined resume and GitHub profiles cross-verify skills and projects."""

    def test_cross_validation_boosts_confidence(self):
        agent = _make_agent()
        req = _resume_github_request()

        report = agent.analyze(req)
        self.assertIsNotNone(report)

        # Python and SQL exist in both resume and github. They should be verified.
        python_ev = next((s for s in report.verified_skills if s.skill == "Python"), None)
        self.assertIsNotNone(python_ev)
        self.assertTrue(python_ev.verified)
        self.assertIn(EvidenceSource.RESUME, python_ev.sources)
        self.assertIn(EvidenceSource.GITHUB, python_ev.sources)
        self.assertEqual(python_ev.confidence, 1.0)  # 2 * 0.40 + 0.20 = 1.0

        # Docker was claimed in resume but is missing from github languages
        docker_ev = next((s for s in report.verified_skills if s.skill == "Docker"), None)
        self.assertIsNotNone(docker_ev)
        self.assertFalse(docker_ev.verified)
        self.assertNotEqual(docker_ev.discrepancy, "")  # Discrepancy should be reported


class TestResumeDocuments(unittest.TestCase):
    """Resume and Document correlation checks."""

    def test_document_correlation(self):
        agent = _make_agent()
        req = _resume_documents_request()

        report = agent.analyze(req)
        self.assertIsNotNone(report)

        # Document topics include "kubernetes administration" and "container architecture"
        # Claimed certification includes "CKA"
        # Skill gaps should list missing backend/devops skills or match them.
        self.assertIsNotNone(report.portfolio_analysis)
        self.assertEqual(report.portfolio_analysis.documentation_score, 33.3)  # 2 topics out of 6


class TestCompletePortfolio(unittest.TestCase):
    """High-quality full portfolio should yield excellent scores."""

    def test_complete_portfolio(self):
        agent = _make_agent()
        req = _complete_portfolio_request()

        report = agent.analyze(req)
        self.assertIsNotNone(report)

        score = report.professional_score
        self.assertIsNotNone(score)
        self.assertIn(score.tier, [ProfessionalTier.PROFICIENT, ProfessionalTier.EXPERT, ProfessionalTier.PRINCIPAL])
        self.assertIsNotNone(report.growth_prediction)
        self.assertEqual(report.growth_prediction.growth_velocity, "moderate")

        # Roadmap, career readiness, and recommendations should be populated
        self.assertIsNotNone(report.learning_roadmap)
        self.assertGreater(len(report.recommendations), 0)


class TestLargeProfilePerformance(unittest.TestCase):
    """Large portfolio with many skills and repos compiles within performance budget."""

    def test_large_profile_budget(self):
        agent = _make_agent()
        large_skills = [
            "Python", "FastAPI", "Go", "Rust", "TypeScript", "React", "Vue", "Docker",
            "Kubernetes", "AWS", "GCP", "Terraform", "Ansible", "SQL", "NoSQL", "Redis",
            "Kafka", "GraphQL", "Git", "CI/CD", "Prometheus", "ELK", "Linux", "Bash"
        ]
        req = ProfessionalAnalysisRequest(
            workspace_id="ws-large-profile",
            resume_name="Frank Large",
            resume_current_role="Staff DevOps Architect",
            resume_years_experience=15.0,
            resume_skills=large_skills,
            github_username="frank_large",
            github_languages=["Go", "Python", "Rust", "TypeScript", "Shell"],
            github_projects=["k8s-operator", "rust-compiler", "wasm-engine", "infra-automation"],
            resume_certifications=["AWS Solutions Architect Professional", "CKA", "LFCS"],
            document_topics=["distributed systems", "kubernetes scaling", "cloud architecture"],
            target_role="Principal Architect",
            target_skills=["Go", "Kubernetes", "Cloud Design", "Security", "Scale"],
        )

        start = time.perf_counter()
        report = agent.analyze(req)
        duration = time.perf_counter() - start

        self.assertIsNotNone(report)
        self.assertLess(duration, 2.0, "Large professional profile analysis exceeded 2-second budget.")
        self.assertEqual(report.professional_score.tier, ProfessionalTier.EXPERT)


class TestScoreWeights(unittest.TestCase):
    """Overriding default scorer weights alters the computed output score."""

    def test_custom_weights(self):
        from backend.intelligence.professional.professional_score import ProfessionalScorer
        profile = _make_agent().build_profile(_resume_github_request())

        # Scoring with default weights
        scorer_default = ProfessionalScorer()
        portfolio = _make_agent()._portfolio_analyzer.analyze(profile, _resume_github_request())
        verified = _make_agent()._reasoner.verify_skills(profile, profile.skills)
        score_default = scorer_default.score(profile, portfolio, verified)

        # Overriding weights to prioritize consistency and career readiness heavily
        custom_weights = {
            "resume_quality": 0.05,
            "github_quality": 0.05,
            "project_depth": 0.05,
            "documentation": 0.05,
            "skill_evidence": 0.05,
            "technology_breadth": 0.05,
            "consistency": 0.40,
            "career_readiness": 0.30,
        }
        scorer_custom = ProfessionalScorer(weights=custom_weights)
        score_custom = scorer_custom.score(profile, portfolio, verified)

        self.assertNotEqual(score_default.overall, score_custom.overall)


class TestReportRetrieval(unittest.TestCase):
    """Saving and retrieving professional reports from the registry."""

    def test_report_retrieval(self):
        agent = _make_agent()
        req = _resume_only_request()
        report = agent.analyze(req)

        retrieved = agent.get_report(report.report_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.report_id, report.report_id)

        # Non-existent report retrieval
        self.assertIsNone(agent.get_report("pr-invalid"))


if __name__ == "__main__":
    unittest.main()
