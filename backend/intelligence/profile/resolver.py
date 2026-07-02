"""Conflict resolution policies for deduplicating skills and source attributions."""

from datetime import datetime
from typing import Optional

from backend.intelligence.profile.models import ProfileSkill, ProfileSource


class ConflictResolver:
    """Combines evidence, updates timestamps, and averages/selects highest confidence scores."""

    def resolve_skill(self, current: Optional[ProfileSkill], new_skill: ProfileSkill) -> ProfileSkill:
        """Deduplicates and merges two skill references.

        Args:
            current: Extracted skill in profile database.
            new_skill: New incoming parsed skill.

        Returns:
            ProfileSkill: Mapped canonical skill.
        """
        if not current:
            return new_skill

        # Deduplicate sources and evidence
        sources = list(set(current.sources + new_skill.sources))
        evidence = list(set(current.evidence + new_skill.evidence))
        
        # Take the maximum confidence score
        confidence = max(current.confidence_score, new_skill.confidence_score)
        
        # Category preference: keep category if already set
        category = current.category or new_skill.category

        return ProfileSkill(
            name=current.name,
            category=category,
            confidence_score=confidence,
            sources=sources,
            evidence=evidence,
            last_updated=datetime.utcnow().isoformat()
        )

    def resolve_source(self, current: Optional[ProfileSource], new_src: ProfileSource) -> ProfileSource:
        """Merges source attribution entries."""
        if not current:
            return new_src

        # Combine evidence
        evidence = current.evidence
        if new_src.evidence:
            evidence = f"{current.evidence} | {new_src.evidence}" if current.evidence else new_src.evidence

        return ProfileSource(
            source_name=current.source_name,
            confidence_score=max(current.confidence_score, new_src.confidence_score),
            extracted_at=new_src.extracted_at,
            evidence=evidence
        )
