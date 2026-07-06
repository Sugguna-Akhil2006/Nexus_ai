"""Orchestrates the full career analysis pipeline."""

from datetime import datetime
from typing import Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.intelligence.career.models import (
    CareerAnalysisRequest,
    CareerProfile,
    CareerReport,
    CareerRoadmap,
    JobMatchResult,
)
from backend.intelligence.career.career_gap_analyzer import CareerGapAnalyzer
from backend.intelligence.career.career_reasoner import CareerReasoner
from backend.intelligence.career.career_recommendation import CareerRecommendationEngine
from backend.intelligence.career.roadmap_generator import RoadmapGenerator
from backend.intelligence.career.job_matcher import JobMatcher
from backend.intelligence.career.career_report import CareerReportBuilder


class CareerService:
    """Orchestrates gap analysis, reasoning, recommendations, roadmap, and report assembly.

    This service never implements intelligence logic itself — it composes
    existing subsystems and wires their outputs together.
    """

    def __init__(self) -> None:
        self._gap_analyzer = CareerGapAnalyzer()
        self._reasoner = CareerReasoner()
        self._rec_engine = CareerRecommendationEngine()
        self._roadmap_gen = RoadmapGenerator()
        self._job_matcher = JobMatcher()
        self._report_builder = CareerReportBuilder()
        self._event_bus = EventBus()

    def analyze(self, request: CareerAnalysisRequest) -> CareerReport:
        """Runs the full career analysis pipeline and returns a CareerReport.

        Pipeline:
            1. Publish ``career.analysis.started``
            2. Perform gap analysis
            3. Generate recommendations and roadmap
            4. Reason over strengths and gaps
            5. Optionally run job matching
            6. Assemble and persist report
            7. Publish ``career.analysis.completed``

        Args:
            request: A ``CareerAnalysisRequest`` with profile and target data.

        Returns:
            A complete ``CareerReport``.
        """
        profile = request.profile

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CareerService",
            payload={
                "event": "career.analysis.started",
                "profile_id": profile.profile_id,
                "workspace_id": request.workspace_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        # 1. Gap analysis
        gaps = self._gap_analyzer.analyze(profile, request.target_skills)

        # 2. Recommendations and roadmap
        recommendations = self._rec_engine.generate(profile, gaps)
        roadmap = self._roadmap_gen.generate(profile, gaps, target_role=request.target_role)

        # 3. Reasoning
        strengths = self._reasoner.reason_about_strengths(profile)
        gap_narrative = self._reasoner.reason_about_gaps(gaps)

        # 4. Optional job matching
        job_match: Optional[JobMatchResult] = None
        if request.job_description:
            job_match = self._job_matcher.match(
                profile,
                request.job_description,
                job_title=request.target_role,
            )

        # 5. Assemble report
        report = self._report_builder.build(
            profile=profile,
            strengths=strengths,
            gap_narrative=gap_narrative,
            gaps=gaps,
            roadmap=roadmap,
            recommendations=recommendations,
            job_match=job_match,
        )

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CareerService",
            payload={
                "event": "career.analysis.completed",
                "profile_id": profile.profile_id,
                "report_id": report.report_id,
                "gap_count": len(gaps),
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

        return report

    def get_report(self, report_id: str) -> Optional[CareerReport]:
        """Retrieves a previously generated career report by ID."""
        return self._report_builder.get(report_id)
