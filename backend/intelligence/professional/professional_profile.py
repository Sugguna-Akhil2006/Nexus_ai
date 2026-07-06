"""Merges multi-source data into a unified CareerProfile for downstream modules."""

from backend.intelligence.career.models import CareerProfile
from backend.intelligence.professional.models import ProfessionalAnalysisRequest


class ProfessionalProfileBuilder:
    """Constructs a unified ``CareerProfile`` from a ``ProfessionalAnalysisRequest``.

    Acts as the entry point for the professional pipeline — all data from
    resume, GitHub, and documents is consolidated here so that downstream
    modules operate on a single consistent view of the candidate.
    """

    def build(self, request: ProfessionalAnalysisRequest) -> CareerProfile:
        """Merges request data into a ``CareerProfile``.

        Deduplicates skills across resume, GitHub languages, and document
        topics so downstream gap analysis and scoring work on clean data.

        Args:
            request: A ``ProfessionalAnalysisRequest`` with all raw inputs.

        Returns:
            A unified ``CareerProfile`` ready for Career Intelligence analysis.
        """
        # Merge and deduplicate all skill-like evidence
        seen: set = set()
        merged_skills = []
        for skill in request.resume_skills:
            key = skill.lower().strip()
            if key not in seen:
                seen.add(key)
                merged_skills.append(skill)

        # GitHub languages treated as additional skill evidence
        github_langs = list(dict.fromkeys(
            lang for lang in request.github_languages if lang.lower().strip() not in seen
        ))

        return CareerProfile(
            workspace_id=request.workspace_id,
            name=request.resume_name,
            current_role=request.resume_current_role,
            years_experience=request.resume_years_experience,
            skills=merged_skills,
            github_languages=request.github_languages,
            github_projects=request.github_projects,
            certifications=request.resume_certifications,
            education=request.resume_education,
            document_topics=request.document_topics,
        )
