"""Top-level Career Intelligence Agent — the public API facade for this module."""

from typing import List, Optional

from backend.intelligence.career.models import (
    CareerAnalysisRequest,
    CareerProfile,
    CareerReport,
    CareerRoadmap,
    JobMatchResult,
)
from backend.intelligence.career.career_service import CareerService
from backend.intelligence.career.career_gap_analyzer import CareerGapAnalyzer
from backend.intelligence.career.roadmap_generator import RoadmapGenerator
from backend.intelligence.career.job_matcher import JobMatcher


class CareerAgent:
    """Flagship Career Intelligence Agent combining all career analysis capabilities.

    Exposes a clean, high-level API that orchestrates the underlying service
    and sub-modules without exposing their internal structure.
    """

    def __init__(self) -> None:
        self._service = CareerService()
        self._gap_analyzer = CareerGapAnalyzer()
        self._roadmap_gen = RoadmapGenerator()
        self._job_matcher = JobMatcher()

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def analyze(self, request: CareerAnalysisRequest) -> CareerReport:
        """Runs the full career intelligence pipeline.

        Args:
            request: Input payload including profile, target role, and optional
                     job description.

        Returns:
            A complete ``CareerReport`` with strengths, gaps, roadmap, and
            recommendations.
        """
        return self._service.analyze(request)

    def generate_roadmap(
        self,
        profile: CareerProfile,
        target_skills: List[str],
        target_role: str = "",
    ) -> CareerRoadmap:
        """Generates a standalone development roadmap for a profile.

        Args:
            profile: The candidate's career profile.
            target_skills: Skills the candidate needs to acquire.
            target_role: Human-readable target role label.

        Returns:
            A ``CareerRoadmap`` with ordered steps and timeline.
        """
        gaps = self._gap_analyzer.analyze(profile, target_skills)
        return self._roadmap_gen.generate(profile, gaps, target_role=target_role)

    def match_job(
        self,
        profile: CareerProfile,
        job_description: str,
        job_title: str = "",
    ) -> JobMatchResult:
        """Compares a profile against a job description.

        Args:
            profile: The candidate's career profile.
            job_description: Raw job posting text.
            job_title: Human-readable job title.

        Returns:
            A ``JobMatchResult`` with match %, missing skills, and improvements.
        """
        return self._job_matcher.match(profile, job_description, job_title)

    def get_report(self, report_id: str) -> Optional[CareerReport]:
        """Retrieves a previously generated career report.

        Args:
            report_id: The report's unique identifier.

        Returns:
            The ``CareerReport`` or ``None`` if not found.
        """
        return self._service.get_report(report_id)
