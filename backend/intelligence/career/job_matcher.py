"""Compares a career profile against a job description to produce a match result."""

import re
from typing import List, Set
from backend.intelligence.career.models import CareerProfile, JobMatchResult


class JobMatcher:
    """Scores how well a CareerProfile aligns with a job description."""

    def match(
        self,
        profile: CareerProfile,
        job_description: str,
        job_title: str = "",
    ) -> JobMatchResult:
        """Compares profile skills against the job description.

        Tokenises the job description into meaningful terms and computes
        a Jaccard-style match percentage against the combined profile skill set.

        Args:
            profile: The candidate's career profile.
            job_description: Raw job description text.
            job_title: Human-readable job title for the result.

        Returns:
            A ``JobMatchResult`` with match %, missing skills, and improvement hints.
        """
        # 1. Extract candidate skills (combined set)
        candidate_skills: Set[str] = {
            s.lower().strip()
            for s in profile.skills + profile.github_languages + profile.certifications
        }

        # 2. Extract job keywords (4–20 char alpha-words, deduped)
        job_tokens: List[str] = list(dict.fromkeys(
            t.lower()
            for t in re.findall(r"\b[a-zA-Z][a-zA-Z0-9#+\-.]{2,19}\b", job_description)
            if len(t) >= 3
        ))

        if not job_tokens:
            return JobMatchResult(
                profile_id=profile.profile_id,
                job_title=job_title,
                skill_match_pct=0.0,
            )

        # 3. Match tokens against candidate skills (substring match)
        matched: List[str] = []
        missing: List[str] = []
        seen_job_terms: Set[str] = set()

        for token in job_tokens:
            if token in seen_job_terms:
                continue
            seen_job_terms.add(token)

            is_matched = any(
                token in cs or cs in token
                for cs in candidate_skills
            )
            if is_matched:
                matched.append(token)
            else:
                missing.append(token)

        total = len(seen_job_terms)
        match_pct = round((len(matched) / total) * 100, 1) if total else 0.0

        # 4. Improvement suggestions
        resume_improvements: List[str] = []
        github_improvements: List[str] = []
        project_suggestions: List[str] = []

        for skill in missing[:5]:
            resume_improvements.append(
                f"Add '{skill}' to resume if you have any related experience."
            )
            github_improvements.append(
                f"Create or contribute to a '{skill}' project on GitHub."
            )
            project_suggestions.append(
                f"Build a demonstrable '{skill}' project."
            )

        return JobMatchResult(
            profile_id=profile.profile_id,
            job_title=job_title,
            skill_match_pct=match_pct,
            matched_skills=matched,
            missing_skills=missing[:10],
            resume_improvements=resume_improvements,
            github_improvements=github_improvements,
            recommended_projects=project_suggestions,
        )
