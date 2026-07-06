"""Cross-source skill and project verification via the Unified Reasoning Engine."""

from typing import List

from backend.intelligence.career.models import CareerProfile
from backend.intelligence.professional.models import EvidenceSource, SkillEvidence
from backend.intelligence.reasoning.reasoning_engine import UnifiedReasoningEngine
from backend.intelligence.reasoning.models import ReasoningRequest


class ProfessionalReasoner:
    """Verifies skills and projects across resume, GitHub, and document sources.

    Delegates all reasoning to ``UnifiedReasoningEngine`` — no logic is
    duplicated here beyond routing evidence to the correct source labels.
    """

    def __init__(self) -> None:
        self._engine = UnifiedReasoningEngine()

    # ------------------------------------------------------------------
    # Skill verification
    # ------------------------------------------------------------------

    def verify_skills(
        self,
        profile: CareerProfile,
        claimed_skills: List[str],
    ) -> List[SkillEvidence]:
        """Checks each claimed skill against all available evidence sources.

        A skill is considered **verified** when it appears in at least two
        independent sources (resume + GitHub, or resume + docs).
        Confidence increases with each corroborating source.
        A discrepancy is flagged when a skill is in resume but absent from
        GitHub languages when GitHub data is present.

        Args:
            profile: The unified career profile containing all data.
            claimed_skills: Skills explicitly listed in the resume.

        Returns:
            List of ``SkillEvidence`` records with verification results.
        """
        github_skills = {s.lower() for s in profile.github_languages}
        doc_topics = {t.lower() for t in profile.document_topics}
        has_github = bool(github_skills)
        has_docs = bool(doc_topics)

        evidences: List[SkillEvidence] = []
        for skill in claimed_skills:
            key = skill.lower().strip()
            sources: List[EvidenceSource] = [EvidenceSource.RESUME]  # claimed in resume
            discrepancy = ""

            if has_github:
                # Partial match: any github language containing or contained in skill key
                matched_gh = any(key in gh or gh in key for gh in github_skills)
                if matched_gh:
                    sources.append(EvidenceSource.GITHUB)
                else:
                    discrepancy = (
                        f"'{skill}' claimed in resume but not evidenced in GitHub languages."
                    )

            if has_docs:
                matched_doc = any(key in dt or dt in key for dt in doc_topics)
                if matched_doc:
                    sources.append(EvidenceSource.DOCUMENT)

            n_sources = len(sources)
            confidence = round(min(1.0, n_sources * 0.40 + 0.20), 2)
            verified = n_sources >= 2

            evidences.append(SkillEvidence(
                skill=skill,
                verified=verified,
                sources=sources,
                confidence=confidence,
                discrepancy=discrepancy,
            ))

        return evidences

    # ------------------------------------------------------------------
    # Project verification
    # ------------------------------------------------------------------

    def verify_projects(self, profile: CareerProfile) -> List[str]:
        """Returns projects evidenced by GitHub (treated as ground truth).

        Args:
            profile: The unified career profile.

        Returns:
            List of verified project names from GitHub.
        """
        return list(profile.github_projects)

    # ------------------------------------------------------------------
    # Consistency narrative
    # ------------------------------------------------------------------

    def reason_about_consistency(
        self,
        verified_skills: List[SkillEvidence],
        workspace_id: str = "professional",
    ) -> str:
        """Generates a consistency narrative across data sources.

        Args:
            verified_skills: List of ``SkillEvidence`` records.
            workspace_id: Workspace context for the reasoning engine.

        Returns:
            Human-readable consistency assessment string.
        """
        discrepancies = [e for e in verified_skills if e.discrepancy]
        verified = [e for e in verified_skills if e.verified]

        evidence_items = [
            f"Verified: {e.skill} ({len(e.sources)} sources)" for e in verified[:5]
        ] + [
            f"Discrepancy: {e.discrepancy}" for e in discrepancies[:3]
        ]

        if not evidence_items:
            return "Insufficient data to assess cross-source consistency."

        request = ReasoningRequest(
            workspace_id=workspace_id,
            query="Assess the consistency of professional claims across resume, GitHub, and documents.",
            evidence=evidence_items,
            context={
                "verified_count": len(verified),
                "discrepancy_count": len(discrepancies),
            },
        )
        report = self._engine.execute_reasoning(request)

        if report.final_conclusions:
            return " ".join(report.final_conclusions)

        if discrepancies:
            skills = ", ".join(e.skill for e in discrepancies[:3])
            return (
                f"{len(verified)} skill(s) verified across sources. "
                f"{len(discrepancies)} discrepancy(s) detected: {skills}."
            )
        return f"All {len(verified)} claimed skill(s) are consistent across available sources."
