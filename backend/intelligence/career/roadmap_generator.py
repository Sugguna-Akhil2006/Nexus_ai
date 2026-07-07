"""Converts ordered skill gaps into a personalised career development roadmap."""

from datetime import datetime
from typing import List

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.career.models import (
    CareerProfile,
    CareerRoadmap,
    CareerRoadmapStep,
    SkillGap,
)

# Static resource suggestions per skill keyword
_RESOURCES: dict = {
    "python": ["docs.python.org", "realpython.com"],
    "docker": ["docs.docker.com", "play-with-docker.com"],
    "kubernetes": ["kubernetes.io/docs", "killercoda.com"],
    "fastapi": ["fastapi.tiangolo.com", "testdriven.io/fastapi"],
    "sql": ["sqlzoo.net", "pgexercises.com"],
    "machine learning": ["fast.ai", "coursera.org/learn/machine-learning"],
    "react": ["react.dev", "scrimba.com/react"],
    "typescript": ["typescriptlang.org/docs", "executeprogram.com/courses/typescript"],
    "aws": ["skillbuilder.aws", "acloudguru.com"],
    "rust": ["doc.rust-lang.org/book", "rustlings.cool"],
}

_DEFAULT_WEEKS = 4


class RoadmapGenerator:
    """Builds a CareerRoadmap from an ordered list of skill gaps."""

    def __init__(self) -> None:
        self._event_bus = EventBus()

    def generate(
        self,
        profile: CareerProfile,
        gaps: List[SkillGap],
        target_role: str = "",
    ) -> CareerRoadmap:
        """Converts skill gaps into an ordered development roadmap.

        Args:
            profile: The candidate's career profile.
            gaps: Ranked ``SkillGap`` list (highest priority first).
            target_role: The role the candidate is working toward.

        Returns:
            A complete ``CareerRoadmap`` with steps, timeline, and summary.
        """
        steps: List[CareerRoadmapStep] = []
        total_weeks = 0

        for i, gap in enumerate(gaps, start=1):
            skill_key = gap.skill.lower()
            resources = _RESOURCES.get(skill_key, [f"Search online tutorials for {gap.skill}"])
            weeks = _DEFAULT_WEEKS + (i % 3)  # slight variation to feel realistic

            step = CareerRoadmapStep(
                step_number=i,
                skill=gap.skill,
                action=f"Study and practise {gap.skill} through structured resources and projects.",
                resources=resources,
                estimated_weeks=weeks,
                expected_outcome=(
                    f"Achieve {gap.target_level.value.lower()} proficiency in {gap.skill}, "
                    f"demonstrable via a portfolio project."
                ),
            )
            steps.append(step)
            total_weeks += weeks

        role_label = target_role or "target role"
        summary = (
            f"This roadmap covers {len(steps)} skill area(s) over ~{total_weeks} weeks, "
            f"guiding {profile.name or 'the candidate'} toward {role_label}."
        )

        roadmap = CareerRoadmap(
            profile_id=profile.profile_id,
            target_role=role_label,
            steps=steps,
            total_estimated_weeks=total_weeks,
            summary=summary,
        )

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="RoadmapGenerator",
            payload={
                "event": "career.roadmap.generated",
                "profile_id": profile.profile_id,
                "steps": len(steps),
                "total_weeks": total_weeks,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        return roadmap
