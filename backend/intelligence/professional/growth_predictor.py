"""Estimates short- and medium-term professional growth from score and profile."""

from typing import List

from backend.intelligence.career.models import CareerProfile
from backend.intelligence.professional.models import GrowthProjection, ProfessionalScore, ProfessionalTier

# ---------------------------------------------------------------------------
# Progression tables
# ---------------------------------------------------------------------------

# Maps (current_tier, years_exp_band) → (6-month projection, 12-month projection)
_PROGRESSION: dict = {
    (ProfessionalTier.EMERGING, "0-1"):   ("Junior Developer", "Junior-Mid Developer"),
    (ProfessionalTier.EMERGING, "1-3"):   ("Junior-Mid Developer", "Mid Developer"),
    (ProfessionalTier.DEVELOPING, "0-1"): ("Junior Developer", "Mid Developer"),
    (ProfessionalTier.DEVELOPING, "1-3"): ("Mid Developer", "Mid-Senior Developer"),
    (ProfessionalTier.DEVELOPING, "3+"):  ("Mid-Senior Developer", "Senior Developer"),
    (ProfessionalTier.PROFICIENT, "0-1"): ("Mid Developer", "Senior Developer"),
    (ProfessionalTier.PROFICIENT, "1-3"): ("Senior Developer", "Senior Developer"),
    (ProfessionalTier.PROFICIENT, "3+"):  ("Senior Developer", "Lead / Staff Engineer"),
    (ProfessionalTier.EXPERT, "0-1"):     ("Senior Developer", "Lead Engineer"),
    (ProfessionalTier.EXPERT, "1-3"):     ("Lead Engineer", "Lead / Principal Engineer"),
    (ProfessionalTier.EXPERT, "3+"):      ("Lead / Principal Engineer", "Principal Engineer"),
    (ProfessionalTier.PRINCIPAL, "3+"):   ("Principal Engineer", "Staff / Distinguished Engineer"),
}

_DEFAULT_PROJECTION = ("Mid Developer", "Senior Developer")


def _years_band(years: float) -> str:
    if years < 1:
        return "0-1"
    elif years < 3:
        return "1-3"
    return "3+"


def _growth_velocity(score: float, years: float) -> str:
    """Derives a qualitative growth velocity label."""
    if score >= 70 and years < 3:
        return "fast"
    elif score >= 50:
        return "moderate"
    return "slow"


class GrowthPredictor:
    """Projects professional growth trajectory from score and profile data."""

    def predict(
        self,
        profile: CareerProfile,
        score: ProfessionalScore,
    ) -> GrowthProjection:
        """Estimates 6-month and 12-month growth outcomes.

        Uses a lookup table keyed by (tier, years_band) — no LLM required,
        making projections deterministic and unit-testable.

        Also identifies risk factors from score component weaknesses.

        Args:
            profile: The unified career profile.
            score: The computed ``ProfessionalScore``.

        Returns:
            A ``GrowthProjection`` with level labels, milestones, and risks.
        """
        band = _years_band(profile.years_experience)
        key = (score.tier, band)
        proj_6m, proj_12m = _PROGRESSION.get(key, _DEFAULT_PROJECTION)

        current_level = f"{score.tier.value.capitalize()} ({profile.current_role or 'Developer'})"

        # Milestones based on weakest components
        milestones: List[str] = []
        comps = score.components
        if comps.github_quality < 50:
            milestones.append("Publish 3+ GitHub projects with documentation.")
        if comps.skill_evidence < 50:
            milestones.append("Validate skills through portfolio projects or certifications.")
        if comps.documentation < 40:
            milestones.append("Add README and technical writeups to existing projects.")
        if comps.technology_breadth < 40:
            milestones.append("Expand into adjacent technologies (e.g. cloud, containers).")
        if not milestones:
            milestones.append("Continue advancing current trajectory with consistent output.")

        # Risk factors
        risks: List[str] = []
        if comps.consistency < 50:
            risks.append("Skill claims not well-evidenced in GitHub — may raise recruiter concern.")
        if comps.github_quality == 0:
            risks.append("No GitHub activity detected — portfolio is invisible to technical reviewers.")
        if profile.years_experience < 1 and score.overall < 30:
            risks.append("Early career with limited evidence — time and project investment needed.")
        if comps.technology_breadth < 30:
            risks.append("Narrow technology exposure may limit role opportunities.")

        return GrowthProjection(
            current_level=current_level,
            projection_6m=proj_6m,
            projection_12m=proj_12m,
            milestones=milestones,
            risk_factors=risks,
            growth_velocity=_growth_velocity(score.overall, profile.years_experience),
        )
