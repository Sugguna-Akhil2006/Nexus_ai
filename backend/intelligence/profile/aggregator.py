"""Profile Aggregator interface coordinating multiple source data merges."""

from typing import Any, Dict, List

from backend.intelligence.profile.models import KnowledgeProfile
from backend.intelligence.profile.services import ProfileService
from backend.intelligence.resume.models import Resume


class ProfileAggregator:
    """Entry interface executing profile aggregation pipelines."""

    def __init__(self) -> None:
        self.service = ProfileService()

    def aggregate_resume_data(self, profile: KnowledgeProfile, resume: Resume) -> KnowledgeProfile:
        """Aggregates Resume data into the KnowledgeProfile."""
        return self.service.aggregate_resume(profile, resume)

    def aggregate_github_data(
        self,
        profile: KnowledgeProfile,
        repositories: List[Dict[str, Any]],
        languages: List[str]
    ) -> KnowledgeProfile:
        """Aggregates GitHub data into the KnowledgeProfile."""
        return self.service.aggregate_github(profile, repositories, languages)
