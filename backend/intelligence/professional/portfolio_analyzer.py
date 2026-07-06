"""Analyses portfolio completeness, project depth, and documentation quality."""

from backend.intelligence.career.models import CareerProfile
from backend.intelligence.professional.models import (
    PortfolioStrength,
    ProfessionalAnalysisRequest,
)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamps a float into [lo, hi]."""
    return max(lo, min(hi, value))


class PortfolioAnalyzer:
    """Scores portfolio completeness, depth, breadth, and documentation."""

    # Thresholds used for heuristic scoring
    _MAX_PROJECTS = 10
    _MAX_LANGUAGES = 8
    _MAX_DOC_TOPICS = 6
    _MAX_SKILLS = 15

    def analyze(
        self,
        profile: CareerProfile,
        request: ProfessionalAnalysisRequest,
    ) -> PortfolioStrength:
        """Computes per-dimension portfolio scores from profile data.

        Scoring approach (all dimensions 0–100):
        - **Completeness**: ratio of non-empty data sources (resume, GitHub, docs)
        - **Project depth**: GitHub project count relative to ``_MAX_PROJECTS``
        - **Documentation**: document topic count relative to ``_MAX_DOC_TOPICS``
        - **Breadth**: unique language/technology count relative to ``_MAX_LANGUAGES``

        Overall portfolio score = weighted average across all dimensions.

        Args:
            profile: The unified ``CareerProfile``.
            request: The original ``ProfessionalAnalysisRequest``.

        Returns:
            A populated ``PortfolioStrength`` instance.
        """
        # Completeness: count how many source types contributed data
        sources_present = sum([
            bool(request.resume_skills or request.resume_text),
            bool(request.github_languages or request.github_projects),
            bool(request.document_topics or request.document_texts),
        ])
        completeness = _clamp((sources_present / 3.0) * 100)

        # Project depth: number of GitHub projects (capped)
        n_projects = len(profile.github_projects)
        project_depth = _clamp((min(n_projects, self._MAX_PROJECTS) / self._MAX_PROJECTS) * 100)

        # Documentation: number of document topics
        n_docs = len(profile.document_topics)
        documentation = _clamp((min(n_docs, self._MAX_DOC_TOPICS) / self._MAX_DOC_TOPICS) * 100)

        # Breadth: unique languages + skills
        all_techs = set(
            t.lower() for t in profile.github_languages + profile.skills
        )
        breadth = _clamp((min(len(all_techs), self._MAX_LANGUAGES) / self._MAX_LANGUAGES) * 100)

        # Weighted overall (completeness 35%, depth 30%, breadth 20%, docs 15%)
        overall = _clamp(
            completeness * 0.35
            + project_depth * 0.30
            + breadth * 0.20
            + documentation * 0.15
        )

        summary_parts = []
        if sources_present == 3:
            summary_parts.append("Full portfolio: resume, GitHub, and documents provided.")
        elif sources_present == 2:
            summary_parts.append("Partial portfolio: two data sources available.")
        else:
            summary_parts.append("Thin portfolio: only one data source present.")

        if n_projects >= 5:
            summary_parts.append(f"{n_projects} GitHub projects demonstrate active development.")
        elif n_projects > 0:
            summary_parts.append(f"{n_projects} GitHub project(s) present.")
        else:
            summary_parts.append("No GitHub projects detected.")

        return PortfolioStrength(
            completeness_score=round(completeness, 1),
            project_depth_score=round(project_depth, 1),
            documentation_score=round(documentation, 1),
            breadth_score=round(breadth, 1),
            overall_portfolio_score=round(overall, 1),
            summary=" ".join(summary_parts),
        )
