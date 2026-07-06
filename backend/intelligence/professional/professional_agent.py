"""Top-level Professional Intelligence Agent — the flagship public API facade."""

from typing import List, Optional

from backend.intelligence.career.models import CareerProfile
from backend.intelligence.professional.models import (
    ProfessionalAnalysisRequest,
    ProfessionalReport,
    ProfessionalScore,
)
from backend.intelligence.professional.professional_service import ProfessionalService
from backend.intelligence.professional.professional_profile import ProfessionalProfileBuilder
from backend.intelligence.professional.portfolio_analyzer import PortfolioAnalyzer
from backend.intelligence.professional.professional_reasoner import ProfessionalReasoner
from backend.intelligence.professional.professional_score import ProfessionalScorer


class ProfessionalAgent:
    """Flagship Professional Intelligence Agent.

    Unifies Resume, GitHub, Document, and Career intelligence.
    Exposes clean endpoints for analyzing portfolios, scoring candidates,
    verifying skills across multiple sources, and generating the flagship report.
    """

    def __init__(self) -> None:
        self._service = ProfessionalService()
        self._profile_builder = ProfessionalProfileBuilder()
        self._portfolio_analyzer = PortfolioAnalyzer()
        self._reasoner = ProfessionalReasoner()
        self._scorer = ProfessionalScorer()

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def analyze(self, request: ProfessionalAnalysisRequest) -> ProfessionalReport:
        """Performs complete professional profile analysis and generates a report.

        Args:
            request: Full context request including resume, github, and document details.

        Returns:
            A complete ``ProfessionalReport`` with score, verified skills, and roadmap.
        """
        return self._service.analyze(request)

    def build_profile(self, request: ProfessionalAnalysisRequest) -> CareerProfile:
        """Builds a unified profile from the request.

        Args:
            request: Raw multi-source input.

        Returns:
            A unified ``CareerProfile``.
        """
        return self._profile_builder.build(request)

    def score(self, request: ProfessionalAnalysisRequest) -> ProfessionalScore:
        """Calculates a professional score without running full report generation.

        Args:
            request: Inputs containing resume, github, and doc elements.

        Returns:
            A ``ProfessionalScore`` showing weights and component metrics.
        """
        profile = self._profile_builder.build(request)
        portfolio = self._portfolio_analyzer.analyze(profile, request)
        verified_skills = self._reasoner.verify_skills(profile, profile.skills)
        # Note: career_report is not generated for standalone score lookup to remain fast
        return self._scorer.score(profile, portfolio, verified_skills)

    def get_report(self, report_id: str) -> Optional[ProfessionalReport]:
        """Retrieves a previously generated professional report.

        Args:
            report_id: Unique report identifier.

        Returns:
            The ``ProfessionalReport`` if found, else ``None``.
        """
        return self._service.get_report(report_id)
