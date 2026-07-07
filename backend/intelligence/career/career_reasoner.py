"""Wraps the Unified Reasoning Engine to draw career-specific conclusions."""

from typing import List
from backend.intelligence.career.models import CareerProfile, CareerRoadmap, SkillGap
from backend.intelligence.reasoning.reasoning_engine import UnifiedReasoningEngine
from backend.intelligence.reasoning.models import ReasoningRequest


class CareerReasoner:
    """Applies the platform's Reasoning Engine to career evidence.

    All reasoning is delegated to ``UnifiedReasoningEngine`` — no reasoning
    logic is duplicated here.
    """

    def __init__(self) -> None:
        self._engine = UnifiedReasoningEngine()

    def reason_about_strengths(self, profile: CareerProfile) -> List[str]:
        """Identifies professional strengths from the career profile.

        Args:
            profile: The candidate's aggregated career profile.

        Returns:
            List of strength conclusion strings.
        """
        evidence = (
            profile.skills
            + profile.github_languages
            + profile.certifications
            + profile.github_projects
        )
        if not evidence:
            return ["Insufficient profile data to determine strengths."]

        request = ReasoningRequest(
            workspace_id=profile.workspace_id or "career",
            query=f"What are the key professional strengths of {profile.name or 'this candidate'}?",
            evidence=evidence,
            context={"role": profile.current_role, "years": profile.years_experience},
        )
        report = self._engine.execute_reasoning(request)
        return report.final_conclusions or ["Strong technical background identified."]

    def reason_about_gaps(self, gaps: List[SkillGap]) -> str:
        """Produces a prioritised narrative describing identified skill gaps.

        Args:
            gaps: Ordered list of ``SkillGap`` objects.

        Returns:
            Human-readable narrative string.
        """
        if not gaps:
            return "No significant skill gaps detected. Profile aligns well with target role."

        evidence = [f"Missing skill: {g.skill} (priority {g.priority})" for g in gaps[:10]]
        request = ReasoningRequest(
            workspace_id="career",
            query="Summarise the skill gaps and their impact on career progression.",
            evidence=evidence,
            context={"gap_count": len(gaps)},
        )
        report = self._engine.execute_reasoning(request)
        return " ".join(report.final_conclusions) if report.final_conclusions else (
            f"{len(gaps)} skill gap(s) identified. Priority areas: "
            + ", ".join(g.skill for g in gaps[:3]) + "."
        )

    def reason_about_growth(
        self,
        profile: CareerProfile,
        roadmap: CareerRoadmap,
    ) -> str:
        """Projects a growth trajectory based on the profile and planned roadmap.

        Args:
            profile: The candidate's current career profile.
            roadmap: The generated development roadmap.

        Returns:
            A growth trajectory summary string.
        """
        evidence = [f"Planned: {step.action}" for step in roadmap.steps[:5]]
        request = ReasoningRequest(
            workspace_id=profile.workspace_id or "career",
            query="What career growth can be expected after completing this roadmap?",
            evidence=evidence,
            context={
                "current_role": profile.current_role,
                "target_role": roadmap.target_role,
                "weeks": roadmap.total_estimated_weeks,
            },
        )
        report = self._engine.execute_reasoning(request)
        return " ".join(report.final_conclusions) if report.final_conclusions else (
            f"Completing the roadmap in ~{roadmap.total_estimated_weeks} weeks "
            f"is projected to advance the candidate toward {roadmap.target_role}."
        )
