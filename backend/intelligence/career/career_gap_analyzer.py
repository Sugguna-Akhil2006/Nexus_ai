"""Identifies skill gaps between a career profile and a target role."""

from typing import List, Set
from backend.intelligence.career.models import CareerProfile, SkillGap, SkillLevel


# Mapping from experience years to baseline career level
_LEVEL_THRESHOLDS = [
    (0.0, SkillLevel.NONE),
    (0.5, SkillLevel.BEGINNER),
    (2.0, SkillLevel.INTERMEDIATE),
    (5.0, SkillLevel.ADVANCED),
    (8.0, SkillLevel.EXPERT),
]


def _infer_level(years: float) -> SkillLevel:
    """Infers skill level from years of experience."""
    level = SkillLevel.NONE
    for threshold, lvl in _LEVEL_THRESHOLDS:
        if years >= threshold:
            level = lvl
    return level


class CareerGapAnalyzer:
    """Compares a CareerProfile against target skills to identify gaps.

    Uses normalised word-set comparison to match skills case-insensitively
    and detect partial matches (e.g. ``"Python"`` ↔ ``"python3"``).
    """

    def analyze(
        self,
        profile: CareerProfile,
        target_skills: List[str],
    ) -> List[SkillGap]:
        """Computes ranked skill gaps between the profile and target skill set.

        Args:
            profile: The candidate's aggregated career profile.
            target_skills: Skills required for the target role.

        Returns:
            Ordered list of ``SkillGap`` objects, highest priority first.
        """
        # Merge all profile skills (resume + GitHub languages)
        profile_skills: Set[str] = {
            s.lower().strip()
            for s in profile.skills + profile.github_languages + profile.certifications
        }

        current_level = _infer_level(profile.years_experience)
        gaps: List[SkillGap] = []
        priority = 1

        for target in target_skills:
            normalised = target.lower().strip()
            # Partial match: any profile skill that contains or is contained by the target
            matched = any(
                normalised in ps or ps in normalised
                for ps in profile_skills
            )
            if not matched:
                gaps.append(SkillGap(
                    skill=target,
                    current_level=SkillLevel.NONE,
                    target_level=SkillLevel.INTERMEDIATE,
                    priority=priority,
                    rationale=(
                        f"'{target}' was not found in resume, GitHub, or certifications."
                    ),
                ))
                priority += 1

        return gaps

    def all_profile_skills(self, profile: CareerProfile) -> List[str]:
        """Returns the full deduplicated skill list from a profile."""
        seen: Set[str] = set()
        result: List[str] = []
        for s in profile.skills + profile.github_languages + profile.certifications:
            key = s.lower().strip()
            if key not in seen:
                seen.add(key)
                result.append(s)
        return result
