"""Assembles all analysis outputs into a CareerReport and stores it in a registry."""

import threading
from typing import Dict, List, Optional

from backend.intelligence.career.models import (
    CareerLevel,
    CareerProfile,
    CareerRecommendation,
    CareerReport,
    CareerRoadmap,
    JobMatchResult,
    SkillGap,
)


def _infer_career_level(years: float) -> CareerLevel:
    """Maps years of experience to a broad career level."""
    if years < 1:
        return CareerLevel.STUDENT
    elif years < 2:
        return CareerLevel.JUNIOR
    elif years < 5:
        return CareerLevel.MID
    elif years < 8:
        return CareerLevel.SENIOR
    elif years < 12:
        return CareerLevel.LEAD
    return CareerLevel.PRINCIPAL


def _build_timeline(roadmap: Optional[CareerRoadmap]) -> str:
    """Produces a plain-text timeline string from a roadmap."""
    if not roadmap or not roadmap.steps:
        return "No roadmap generated."
    lines = ["Career Development Timeline", "─" * 30]
    cumulative = 0
    for step in roadmap.steps:
        cumulative += step.estimated_weeks
        lines.append(f"Week {cumulative:>3}: {step.skill} — {step.expected_outcome}")
    return "\n".join(lines)


class CareerReportBuilder:
    """Constructs ``CareerReport`` instances and maintains an in-memory store."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, CareerReport] = {}

    def build(
        self,
        profile: CareerProfile,
        strengths: List[str],
        gap_narrative: str,
        gaps: List[SkillGap],
        roadmap: Optional[CareerRoadmap],
        recommendations: List[CareerRecommendation],
        job_match: Optional[JobMatchResult] = None,
    ) -> CareerReport:
        """Assembles a complete ``CareerReport`` from analysis components.

        Args:
            profile: The candidate's career profile.
            strengths: Reasoning-engine conclusion list for strengths.
            gap_narrative: Narrative summary of identified gaps.
            gaps: Ranked list of ``SkillGap`` objects.
            roadmap: Generated ``CareerRoadmap`` (may be ``None``).
            recommendations: Prioritised ``CareerRecommendation`` list.
            job_match: Optional ``JobMatchResult`` if job matching was requested.

        Returns:
            A persisted ``CareerReport`` ready for retrieval.
        """
        level = _infer_career_level(profile.years_experience)
        weaknesses = [g.skill for g in gaps[:5]]
        timeline = _build_timeline(roadmap)

        summary_parts = [
            f"{profile.name or 'The candidate'} is at {level.value} level "
            f"with {profile.years_experience:.1f} years of experience.",
        ]
        if strengths:
            summary_parts.append(f"Key strengths: {', '.join(strengths[:3])}.")
        if gap_narrative:
            summary_parts.append(gap_narrative)

        report = CareerReport(
            workspace_id=profile.workspace_id,
            profile_id=profile.profile_id,
            career_level=level,
            executive_summary=" ".join(summary_parts),
            strengths=strengths,
            weaknesses=weaknesses,
            skill_gaps=gaps,
            roadmap=roadmap,
            recommendations=recommendations,
            job_match=job_match,
            career_timeline=timeline,
        )

        with self._lock:
            self._store[report.report_id] = report

        return report

    def get(self, report_id: str) -> Optional[CareerReport]:
        """Retrieves a previously built ``CareerReport`` by ID."""
        with self._lock:
            return self._store.get(report_id)

    def list_all(self) -> List[CareerReport]:
        """Returns all stored career reports."""
        with self._lock:
            return list(self._store.values())
