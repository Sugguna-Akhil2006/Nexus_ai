"""Computes the weighted Professional Score (0–100) from all analysis components."""

from datetime import datetime
from typing import Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.career.models import CareerProfile, CareerReport
from backend.intelligence.professional.models import (
    DEFAULT_SCORE_WEIGHTS,
    PortfolioStrength,
    ProfessionalScore,
    ProfessionalTier,
    ScoreComponents,
    SkillEvidence,
)


def _tier(score: float) -> ProfessionalTier:
    """Maps a 0–100 score to a ``ProfessionalTier``."""
    if score >= 81:
        return ProfessionalTier.PRINCIPAL
    elif score >= 61:
        return ProfessionalTier.EXPERT
    elif score >= 41:
        return ProfessionalTier.PROFICIENT
    elif score >= 21:
        return ProfessionalTier.DEVELOPING
    return ProfessionalTier.EMERGING


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


class ProfessionalScorer:
    """Calculates a composite professional score from all analysis dimensions."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or dict(DEFAULT_SCORE_WEIGHTS)
        self._event_bus = EventBus()

    def score(
        self,
        profile: CareerProfile,
        portfolio: PortfolioStrength,
        verified_skills: List[SkillEvidence],
        career_report: Optional[CareerReport] = None,
    ) -> ProfessionalScore:
        """Computes the professional score from all available analysis components.

        Scoring heuristics:
        - **resume_quality**: scales with skill count and years of experience
        - **github_quality**: scales with project count and language breadth
        - **project_depth**: taken from portfolio.project_depth_score
        - **documentation**: taken from portfolio.documentation_score
        - **skill_evidence**: average confidence across verified skills
        - **technology_breadth**: taken from portfolio.breadth_score
        - **consistency**: penalised by discrepancy count in verified_skills
        - **career_readiness**: derived from career report gap count (if available)
        - **confidence_score**: mean confidence of all skill evidence

        Args:
            profile: The unified career profile.
            portfolio: Portfolio strength analysis result.
            verified_skills: Cross-source skill verification records.
            career_report: Optional career analysis report for gap data.

        Returns:
            A ``ProfessionalScore`` with all component values and tier.
        """
        # Resume quality (skills count + years experience)
        resume_q = _clamp(
            min(len(profile.skills), 20) / 20 * 60
            + min(profile.years_experience, 10) / 10 * 40
        )

        # GitHub quality (projects + language breadth)
        github_q = _clamp(
            min(len(profile.github_projects), 10) / 10 * 60
            + min(len(profile.github_languages), 8) / 8 * 40
        )

        # Project depth and documentation from portfolio
        proj_depth = portfolio.project_depth_score
        docs = portfolio.documentation_score
        breadth = portfolio.breadth_score

        # Skill evidence: mean confidence
        if verified_skills:
            skill_ev = _clamp(
                (sum(e.confidence for e in verified_skills) / len(verified_skills)) * 100
            )
        else:
            skill_ev = 0.0

        # Consistency: penalise for each discrepancy
        n_discrepancies = sum(1 for e in verified_skills if e.discrepancy)
        n_total = max(len(verified_skills), 1)
        consistency = _clamp(
            100 - (n_discrepancies / n_total) * 100
        )

        # Career readiness: from gap count (fewer gaps = higher readiness)
        if career_report:
            gap_count = len(career_report.skill_gaps)
            career_ready = _clamp(100 - gap_count * 10)
        else:
            career_ready = 50.0  # neutral when no career report

        # Confidence: mean of all verified skill confidences
        conf = skill_ev  # reuse skill evidence confidence as overall confidence proxy

        components = ScoreComponents(
            resume_quality=round(resume_q, 1),
            github_quality=round(github_q, 1),
            project_depth=round(proj_depth, 1),
            documentation=round(docs, 1),
            skill_evidence=round(skill_ev, 1),
            technology_breadth=round(breadth, 1),
            consistency=round(consistency, 1),
            career_readiness=round(career_ready, 1),
            confidence_score=round(conf, 1),
        )

        # Weighted overall (exclude confidence_score from total)
        w = self._weights
        overall = _clamp(
            components.resume_quality * w.get("resume_quality", 0.20)
            + components.github_quality * w.get("github_quality", 0.20)
            + components.project_depth * w.get("project_depth", 0.15)
            + components.documentation * w.get("documentation", 0.10)
            + components.skill_evidence * w.get("skill_evidence", 0.15)
            + components.technology_breadth * w.get("technology_breadth", 0.10)
            + components.consistency * w.get("consistency", 0.05)
            + components.career_readiness * w.get("career_readiness", 0.05)
        )

        ps = ProfessionalScore(
            overall=round(overall, 1),
            tier=_tier(overall),
            components=components,
            weights_used=dict(self._weights),
        )

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProfessionalScorer",
            payload={
                "event": "professional.score.generated",
                "workspace_id": profile.workspace_id,
                "score_id": ps.score_id,
                "overall": overall,
                "tier": ps.tier.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        return ps
