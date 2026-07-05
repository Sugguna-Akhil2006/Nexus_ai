"""Scores project maintainability index, release cadences, doc freshness, and overall health."""

from datetime import datetime
from typing import List, Dict, Any
from backend.intelligence.github.models import HealthScores, ReleaseInfo


class RepositoryHealthScorer:
    """Calculates multidimensional project health and velocity scores."""

    def calculate_health_scores(
        self,
        commits: List[Dict[str, Any]],
        releases: List[ReleaseInfo],
        active_contributors: int,
        has_readme: bool,
        doc_readability: float
    ) -> HealthScores:
        """Heuristically computes health score categories on 0-100 scales.

        Args:
            commits: List of commit objects.
            releases: Tag release objects.
            active_contributors: Contributor count.
            has_readme: True if readme exists.
            doc_readability: Readability score of docs.

        Returns:
            HealthScores: Calculated health category scores.
        """
        # 1. Activity Score (based on commit count and frequency in past 30 days)
        activity_score = 50.0
        if commits:
            activity_score = min(100.0, 50.0 + (len(commits) / 5.0))  # 250 commits -> 100 score
            
            # Check days since last commit
            sorted_commits = sorted(commits, key=lambda c: c["timestamp"])
            last_commit_time = sorted_commits[-1]["timestamp"]
            if last_commit_time.tzinfo is not None:
                last_commit_time = last_commit_time.replace(tzinfo=None)
            days_inactive = (datetime.utcnow() - last_commit_time).days
            if days_inactive > 30:
                activity_score = max(10.0, activity_score - (days_inactive - 30) * 2.0)

        # 2. Maintenance Score (high contributors + active releases + clean docs)
        maintenance_score = 60.0
        if active_contributors > 1:
            maintenance_score += 15.0
        if releases:
            maintenance_score += 15.0
        if has_readme:
            maintenance_score += 10.0
        maintenance_score = min(100.0, maintenance_score)

        # 3. Release Cadence Score
        release_cadence_score = 50.0
        if releases:
            # 100 if there are regular releases, or simple tag count scaling
            release_cadence_score = min(100.0, 50.0 + len(releases) * 10)
        else:
            release_cadence_score = 20.0

        # 4. Issue Resolution Score (estimates or mock defaults)
        issue_resolution_score = 75.0

        # 5. Documentation Freshness Score
        documentation_freshness_score = doc_readability if has_readme else 10.0

        # 6. Community Health Score (based on contributor distribution and files present)
        community_health_score = 50.0
        if active_contributors >= 3:
            community_health_score = 90.0
        elif active_contributors == 2:
            community_health_score = 70.0
        else:
            community_health_score = 40.0

        # 7. Overall Health Score (weighted average of category scores)
        overall_health_score = (
            activity_score * 0.25 +
            maintenance_score * 0.25 +
            release_cadence_score * 0.15 +
            issue_resolution_score * 0.10 +
            documentation_freshness_score * 0.15 +
            community_health_score * 0.10
        )

        return HealthScores(
            maintenance_score=round(maintenance_score, 1),
            activity_score=round(activity_score, 1),
            release_cadence_score=round(release_cadence_score, 1),
            issue_resolution_score=round(issue_resolution_score, 1),
            documentation_freshness_score=round(documentation_freshness_score, 1),
            community_health_score=round(community_health_score, 1),
            overall_health_score=round(overall_health_score, 1)
        )
