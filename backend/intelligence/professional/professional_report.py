"""Assembles the ProfessionalReport and maintains an in-memory report registry."""

import threading
from typing import Dict, List, Optional

from backend.intelligence.career.models import CareerReport
from backend.intelligence.professional.models import (
    GrowthProjection,
    PortfolioStrength,
    ProfessionalReport,
    ProfessionalScore,
    SkillEvidence,
)


def _build_evidence_summary(verified_skills: List[SkillEvidence]) -> str:
    """Produces a concise text summary of skill verification results."""
    verified = [e for e in verified_skills if e.verified]
    discrepancies = [e for e in verified_skills if e.discrepancy]
    parts = [
        f"{len(verified_skills)} skill(s) analysed across all data sources.",
        f"{len(verified)} confirmed with multi-source evidence.",
    ]
    if discrepancies:
        names = ", ".join(e.skill for e in discrepancies[:3])
        parts.append(f"{len(discrepancies)} discrepancy(s) detected ({names}).")
    return " ".join(parts)


def _build_executive_summary(
    score: ProfessionalScore,
    portfolio: PortfolioStrength,
    growth: GrowthProjection,
    career_report: CareerReport,
) -> str:
    """Assembles a brief executive summary from all analysis components."""
    parts = [
        f"Professional Score: {score.overall:.0f}/100 ({score.tier.value.capitalize()}).",
        portfolio.summary,
        f"Growth velocity: {growth.growth_velocity}.",
    ]
    if career_report.executive_summary:
        parts.append(career_report.executive_summary)
    return " ".join(parts)


class ProfessionalReportBuilder:
    """Constructs ``ProfessionalReport`` instances and stores them in memory."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, ProfessionalReport] = {}

    def build(
        self,
        workspace_id: str,
        score: ProfessionalScore,
        portfolio: PortfolioStrength,
        verified_skills: List[SkillEvidence],
        verified_projects: List[str],
        growth: GrowthProjection,
        career_report: CareerReport,
        recommendations: list,
        consistency_narrative: str,
    ) -> ProfessionalReport:
        """Assembles and persists a ``ProfessionalReport``.

        Args:
            workspace_id: Originating workspace identifier.
            score: Computed ``ProfessionalScore``.
            portfolio: ``PortfolioStrength`` analysis result.
            verified_skills: Cross-source verification records.
            verified_projects: GitHub-verified project names.
            growth: ``GrowthProjection`` with 6m/12m estimates.
            career_report: Career analysis output.
            recommendations: Merged recommendation list.
            consistency_narrative: Cross-source consistency narrative.

        Returns:
            The persisted ``ProfessionalReport``.
        """
        roadmap_summary = ""
        if career_report.roadmap:
            roadmap_summary = career_report.roadmap.summary

        career_readiness = (
            f"Career Readiness Score: {score.components.career_readiness:.0f}/100. "
            f"{len(career_report.skill_gaps)} skill gap(s) remain."
        )

        executive_summary = _build_executive_summary(score, portfolio, growth, career_report)
        evidence_summary = _build_evidence_summary(verified_skills)

        report = ProfessionalReport(
            workspace_id=workspace_id,
            executive_summary=executive_summary,
            professional_score=score,
            verified_skills=verified_skills,
            verified_projects=verified_projects,
            career_readiness=career_readiness,
            portfolio_analysis=portfolio,
            growth_prediction=growth,
            recommendations=recommendations,
            learning_roadmap=roadmap_summary,
            evidence_summary=evidence_summary,
        )

        with self._lock:
            self._store[report.report_id] = report

        return report

    def get(self, report_id: str) -> Optional[ProfessionalReport]:
        """Retrieves a stored report by ID."""
        with self._lock:
            return self._store.get(report_id)

    def list_all(self) -> list:
        """Returns all stored professional reports."""
        with self._lock:
            return list(self._store.values())
