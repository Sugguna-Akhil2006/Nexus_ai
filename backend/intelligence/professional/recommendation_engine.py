"""Consolidates and deduplicates recommendations from career and professional analyses."""

from typing import Any, Dict, List

from backend.intelligence.career.models import CareerRecommendation, CareerReport
from backend.intelligence.professional.models import ProfessionalScore


class RecommendationEngine:
    """Merges career engine recommendations with professional score gap insights.

    Deduplicates by title and re-ranks by score component weakness so the
    user always sees the most impactful actions first.
    """

    def generate(
        self,
        career_report: CareerReport,
        score: ProfessionalScore,
    ) -> List[CareerRecommendation]:
        """Combines and re-ranks recommendations.

        Args:
            career_report: The career analysis report from ``CareerAgent``.
            score: The computed ``ProfessionalScore``.

        Returns:
            Deduplicated, priority-ordered list of ``CareerRecommendation`` objects.
        """
        # Start with career engine recommendations
        recs: List[CareerRecommendation] = list(career_report.recommendations)

        # Add score-driven recommendations for weak dimensions
        score_recs = self._recs_from_score(score)
        seen_titles: Dict[str, bool] = {r.title.lower(): True for r in recs}

        for rec in score_recs:
            if rec.title.lower() not in seen_titles:
                recs.append(rec)
                seen_titles[rec.title.lower()] = True

        # Re-sort by priority (lowest number = highest priority)
        return sorted(recs, key=lambda r: r.priority)

    def _recs_from_score(self, score: ProfessionalScore) -> List[CareerRecommendation]:
        """Generates additional recommendations from low-scoring components."""
        from backend.intelligence.career.models import RecommendationType
        recs = []
        comps = score.components
        priority = 50  # start below career engine priorities

        if comps.github_quality < 40:
            recs.append(CareerRecommendation(
                rec_type=RecommendationType.PROJECT,
                title="Build and publish 3+ GitHub projects with clear README files.",
                rationale="GitHub quality score is low — visible projects are key for technical credibility.",
                priority=priority,
                estimated_hours=30,
            ))
            priority += 1

        if comps.documentation < 40:
            recs.append(CareerRecommendation(
                rec_type=RecommendationType.LEARNING,
                title="Write technical documentation or a dev blog for existing projects.",
                rationale="Documentation score is low — written communication skills improve hire-ability.",
                priority=priority,
                estimated_hours=10,
            ))
            priority += 1

        if comps.technology_breadth < 40:
            recs.append(CareerRecommendation(
                rec_type=RecommendationType.LEARNING,
                title="Explore a new technology domain (e.g. cloud, containerisation, or data).",
                rationale="Technology breadth is narrow — cross-domain knowledge opens more opportunities.",
                priority=priority,
                estimated_hours=40,
            ))
            priority += 1

        if comps.consistency < 50:
            recs.append(CareerRecommendation(
                rec_type=RecommendationType.PROJECT,
                title="Create GitHub projects that demonstrate skills listed on your resume.",
                rationale="Several resume claims are not evidenced in GitHub — alignment reduces recruiter risk.",
                priority=priority,
                estimated_hours=20,
            ))

        return recs
