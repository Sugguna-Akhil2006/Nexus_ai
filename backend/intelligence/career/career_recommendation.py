"""Generates prioritised career recommendations from skill gaps and profile data."""

from datetime import datetime
from typing import List

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.career.models import (
    CareerProfile,
    CareerRecommendation,
    RecommendationType,
    SkillGap,
)

# ---------------------------------------------------------------------------
# Static resource and project suggestion maps
# ---------------------------------------------------------------------------

_LEARNING_RESOURCES: dict = {
    "python": "Official Python Tutorial (docs.python.org)",
    "fastapi": "FastAPI official docs (fastapi.tiangolo.com)",
    "docker": "Docker Getting Started guide (docs.docker.com)",
    "kubernetes": "Kubernetes Basics (kubernetes.io/docs)",
    "sql": "SQLZoo interactive SQL tutorials",
    "machine learning": "fast.ai Practical Deep Learning course",
    "typescript": "TypeScript Handbook (typescriptlang.org)",
    "react": "React official tutorial (react.dev)",
    "rust": "The Rust Book (doc.rust-lang.org/book)",
    "aws": "AWS Skill Builder free training (skillbuilder.aws)",
}

_PROJECT_SUGGESTIONS: dict = {
    "python": "Build a REST API with FastAPI and deploy on Docker",
    "docker": "Containerise an existing application with multi-stage Dockerfile",
    "kubernetes": "Deploy a microservice on a local Minikube cluster",
    "sql": "Design a relational schema and implement CRUD operations",
    "machine learning": "Train a classification model on a public dataset",
    "typescript": "Migrate a JavaScript project to TypeScript",
    "react": "Build a responsive dashboard with real API data",
    "aws": "Deploy a serverless function using AWS Lambda and API Gateway",
}

_CERT_SUGGESTIONS: dict = {
    "aws": "AWS Certified Developer – Associate",
    "docker": "Docker Certified Associate",
    "kubernetes": "Certified Kubernetes Application Developer (CKAD)",
    "machine learning": "Google Professional Machine Learning Engineer",
    "python": "PCEP – Certified Entry-Level Python Programmer",
    "sql": "Oracle Database SQL Certified Associate",
}


class CareerRecommendationEngine:
    """Produces prioritised project, learning, and certification recommendations."""

    def __init__(self) -> None:
        self._event_bus = EventBus()

    def generate(
        self,
        profile: CareerProfile,
        gaps: List[SkillGap],
    ) -> List[CareerRecommendation]:
        """Generates recommendations ordered by skill gap priority.

        Args:
            profile: The candidate's career profile.
            gaps: Ranked skill gap list from ``CareerGapAnalyzer``.

        Returns:
            Ordered list of ``CareerRecommendation`` instances.
        """
        recs: List[CareerRecommendation] = []

        for gap in gaps[:8]:  # cap at 8 recommendations
            skill_lower = gap.skill.lower()

            # Learning resource recommendation
            resource = _LEARNING_RESOURCES.get(skill_lower, f"Study {gap.skill} via online courses")
            recs.append(CareerRecommendation(
                rec_type=RecommendationType.LEARNING,
                title=f"Learn {gap.skill}",
                rationale=gap.rationale,
                priority=gap.priority,
                estimated_hours=40,
            ))

            # Project recommendation (if available)
            if skill_lower in _PROJECT_SUGGESTIONS:
                recs.append(CareerRecommendation(
                    rec_type=RecommendationType.PROJECT,
                    title=_PROJECT_SUGGESTIONS[skill_lower],
                    rationale=f"Practical application of {gap.skill} strengthens portfolio.",
                    priority=gap.priority,
                    estimated_hours=20,
                ))

            # Certification (if available)
            if skill_lower in _CERT_SUGGESTIONS:
                recs.append(CareerRecommendation(
                    rec_type=RecommendationType.CERTIFICATION,
                    title=_CERT_SUGGESTIONS[skill_lower],
                    rationale=f"Industry-recognised certification validates {gap.skill} expertise.",
                    priority=gap.priority + 1,
                    estimated_hours=60,
                ))

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CareerRecommendationEngine",
            payload={
                "event": "career.recommendation.generated",
                "profile_id": profile.profile_id,
                "recommendation_count": len(recs),
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        return sorted(recs, key=lambda r: r.priority)
