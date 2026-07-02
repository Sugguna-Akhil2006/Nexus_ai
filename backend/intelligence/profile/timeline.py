"""Timeline compilation engine sorting educational and experience events chronologically."""

from typing import List

from backend.intelligence.profile.models import KnowledgeProfile, TimelineEvent


class TimelineEngine:
    """Consolidates education, experience, and projects into a chronological history list."""

    def build_timeline(self, profile: KnowledgeProfile) -> List[TimelineEvent]:
        """Arranges education, experience, and projects in reverse chronological order.

        Args:
            profile: The target KnowledgeProfile.

        Returns:
            List[TimelineEvent]: Chronological timeline events list.
        """
        events: List[TimelineEvent] = []

        # 1. Map Education entries
        for edu in profile.education:
            events.append(TimelineEvent(
                title=f"Studied {edu.degree or 'Degree'} at {edu.institution}",
                event_type="Education",
                organization=edu.institution,
                start_date=None,
                end_date=edu.graduation_year,
                description=f"Field: {edu.branch or 'General'}",
                sources=edu.sources
            ))

        # 2. Map Experience entries
        for exp in profile.experience:
            events.append(TimelineEvent(
                title=f"{exp.role} at {exp.company}",
                event_type="Experience",
                organization=exp.company,
                start_date=exp.start_date,
                end_date=exp.end_date,
                description="\n".join(exp.responsibilities),
                sources=exp.sources
            ))

        # 3. Map Projects
        for proj in profile.projects:
            events.append(TimelineEvent(
                title=f"Built project: {proj.name}",
                event_type="Project",
                organization="Personal",
                start_date=None,
                end_date=None,
                description=proj.description,
                sources=proj.sources
            ))

        # Chronological sort key (descending: Present/latest first)
        def get_sort_key(event: TimelineEvent) -> str:
            date_val = event.end_date or event.start_date or ""
            if "present" in date_val.lower():
                return "9999-12"
            return date_val

        events.sort(key=get_sort_key, reverse=True)
        return events
