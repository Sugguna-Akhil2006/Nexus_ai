"""Orchestrates the full Unified Professional Intelligence pipeline."""

from datetime import datetime
from typing import Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.career.career_agent import CareerAgent
from backend.intelligence.career.models import CareerAnalysisRequest
from backend.intelligence.professional.models import (
    ProfessionalAnalysisRequest,
    ProfessionalReport,
)
from backend.intelligence.professional.professional_profile import ProfessionalProfileBuilder
from backend.intelligence.professional.portfolio_analyzer import PortfolioAnalyzer
from backend.intelligence.professional.professional_reasoner import ProfessionalReasoner
from backend.intelligence.professional.professional_score import ProfessionalScorer
from backend.intelligence.professional.growth_predictor import GrowthPredictor
from backend.intelligence.professional.recommendation_engine import RecommendationEngine
from backend.intelligence.professional.professional_report import ProfessionalReportBuilder


class ProfessionalService:
    """Orchestrates the 8-step unified professional intelligence pipeline.

    Pipeline:
        1. Build unified ``CareerProfile`` (``ProfessionalProfileBuilder``)
        2. Run career analysis (``CareerAgent``)
        3. Analyse portfolio (``PortfolioAnalyzer``)
        4. Verify skills via reasoning (``ProfessionalReasoner``)
        5. Compute professional score (``ProfessionalScorer``)
        6. Predict growth (``GrowthPredictor``)
        7. Merge recommendations (``RecommendationEngine``)
        8. Assemble and persist report (``ProfessionalReportBuilder``)
    """

    def __init__(self) -> None:
        self._profile_builder = ProfessionalProfileBuilder()
        self._career_agent = CareerAgent()
        self._portfolio_analyzer = PortfolioAnalyzer()
        self._reasoner = ProfessionalReasoner()
        self._scorer = ProfessionalScorer()
        self._growth_predictor = GrowthPredictor()
        self._rec_engine = RecommendationEngine()
        self._report_builder = ProfessionalReportBuilder()
        self._event_bus = EventBus()

    def analyze(self, request: ProfessionalAnalysisRequest) -> ProfessionalReport:
        """Runs the full unified professional intelligence pipeline.

        Args:
            request: ``ProfessionalAnalysisRequest`` with all raw inputs.

        Returns:
            A complete ``ProfessionalReport``.
        """
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProfessionalService",
            payload={
                "event": "professional.analysis.started",
                "workspace_id": request.workspace_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        # Step 1: Unified profile
        profile = self._profile_builder.build(request)

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProfessionalService",
            payload={
                "event": "professional.profile.updated",
                "profile_id": profile.profile_id,
                "workspace_id": request.workspace_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        # Step 2: Career analysis (reuses CareerAgent)
        career_req = CareerAnalysisRequest(
            workspace_id=request.workspace_id,
            profile=profile,
            target_role=request.target_role,
            target_skills=request.target_skills,
            job_description=request.job_description,
        )
        career_report = self._career_agent.analyze(career_req)

        # Step 3: Portfolio analysis
        portfolio = self._portfolio_analyzer.analyze(profile, request)

        # Step 4: Skill verification
        claimed_skills = profile.skills
        verified_skills = self._reasoner.verify_skills(profile, claimed_skills)
        verified_projects = self._reasoner.verify_projects(profile)
        consistency_narrative = self._reasoner.reason_about_consistency(
            verified_skills, workspace_id=request.workspace_id
        )

        # Step 5: Professional score
        score = self._scorer.score(
            profile, portfolio, verified_skills, career_report
        )

        # Step 6: Growth prediction
        growth = self._growth_predictor.predict(profile, score)

        # Step 7: Merge recommendations
        recommendations = self._rec_engine.generate(career_report, score)

        # Step 8: Assemble report
        report = self._report_builder.build(
            workspace_id=request.workspace_id,
            score=score,
            portfolio=portfolio,
            verified_skills=verified_skills,
            verified_projects=verified_projects,
            growth=growth,
            career_report=career_report,
            recommendations=recommendations,
            consistency_narrative=consistency_narrative,
        )

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ProfessionalService",
            payload={
                "event": "professional.analysis.completed",
                "workspace_id": request.workspace_id,
                "report_id": report.report_id,
                "score": score.overall,
                "tier": score.tier.value,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        return report

    def get_report(self, report_id: str) -> Optional[ProfessionalReport]:
        """Retrieves a previously generated professional report by ID."""
        return self._report_builder.get(report_id)
