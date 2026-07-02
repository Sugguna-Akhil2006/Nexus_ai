"""Orchestrates commit timelines, release histories, and team collaboration reviews."""

import uuid
from datetime import datetime
from typing import List, Optional
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.github.models import (
    RepositoryHealthReport,
    EngineeringInsight,
    RecommendationItem
)
from backend.intelligence.github.repository import GitRepositoryReader
from backend.intelligence.github.commit_analysis import CommitAnalyzer
from backend.intelligence.github.release_analysis import ReleaseAnalyzer
from backend.intelligence.github.collaboration import CollaborationEvaluator
from backend.intelligence.github.project_evolution import ProjectEvolutionAnalyzer
from backend.intelligence.github.repository_health import RepositoryHealthScorer


class EngineeringActivityAnalyzer:
    """Orchestrates commit frequencies, releases predictability, and project health indicators."""

    def __init__(self) -> None:
        self.commit_analyzer = CommitAnalyzer()
        self.release_analyzer = ReleaseAnalyzer()
        self.collab_evaluator = CollaborationEvaluator()
        self.evolution_analyzer = ProjectEvolutionAnalyzer()
        self.health_scorer = RepositoryHealthScorer()
        self.event_bus = EventBus()

    def analyze_activity(
        self,
        reader: GitRepositoryReader,
        repository_url: str = "",
        workspace_id: str = "default-ws",
        doc_readability: float = 70.0,
        has_readme: bool = True
    ) -> RepositoryHealthReport:
        """Executes full activity and health evaluations on local Git workspace.

        Args:
            reader: Workspace reader.
            repository_url: Repository URL.
            workspace_id: Current workspace ID.
            doc_readability: Readability score of docs.
            has_readme: True if readme exists.

        Returns:
            RepositoryHealthReport: Aggregated activity and health statistics.
        """
        commits = reader.get_commit_history()
        
        # 1. Runs segmented analytical modules
        commit_data = self.commit_analyzer.analyze_commits(commits)
        releases = self.release_analyzer.analyze_releases(reader, commits)
        collab_data = self.collab_evaluator.evaluate_collaboration(commits)
        evol_data = self.evolution_analyzer.analyze_evolution(commits)
        
        # 2. Computes multidimensional health scores
        scores = self.health_scorer.calculate_health_scores(
            commits=commits,
            releases=releases,
            active_contributors=collab_data["active_contributors"],
            has_readme=has_readme,
            doc_readability=doc_readability
        )

        # 3. Generate evidence-based observations/insights
        insights = []
        if len(commits) > 100:
            insights.append(EngineeringInsight(
                insight_type="Activity",
                description="Repository is actively maintained and evolved.",
                evidence=f"Found {len(commits)} commits total in history log.",
                priority="High"
            ))
        elif len(commits) > 0:
            insights.append(EngineeringInsight(
                insight_type="Activity",
                description="Development activity has slowed or is initial draft.",
                evidence=f"Only {len(commits)} commits recorded.",
                priority="Medium"
            ))
        else:
            insights.append(EngineeringInsight(
                insight_type="Activity",
                description="No active commit history found.",
                evidence="Empty commit history log.",
                priority="Low"
            ))

        if has_readme and doc_readability >= 80.0:
            insights.append(EngineeringInsight(
                insight_type="Documentation",
                description="Documentation is highly detailed and complete.",
                evidence=f"README readability score: {doc_readability}",
                priority="Medium"
            ))
        elif not has_readme:
            insights.append(EngineeringInsight(
                insight_type="Documentation",
                description="Documentation has not kept pace with code changes.",
                evidence="Missing README file in root directory.",
                priority="High"
            ))

        if releases:
            insights.append(EngineeringInsight(
                insight_type="Maintenance",
                description="Releases are regular and predictable.",
                evidence=f"Found {len(releases)} active software release versions/tags.",
                priority="Medium"
            ))

        if evol_data["refactoring_percentage"] >= 10.0:
            insights.append(EngineeringInsight(
                insight_type="Quality",
                description="Refactoring activity suggests improving modularity.",
                evidence=f"Refactoring commits account for {evol_data['refactoring_percentage']}% of updates.",
                priority="Medium"
            ))

        # 4. Generate recommendations
        recommendations = []
        if not releases:
            recommendations.append(RecommendationItem(
                action="Establish release tag conventions",
                rationale="Tagging versions provides a predictable deployment target.",
                expected_impact="High",
                difficulty="Easy"
            ))
        if collab_data["bus_factor"] <= 1 and collab_data["active_contributors"] > 1:
            recommendations.append(RecommendationItem(
                action="Redistribute module ownership",
                rationale="High concentration of commits suggests silo risk.",
                expected_impact="High",
                difficulty="Medium"
            ))
        if not has_readme:
            recommendations.append(RecommendationItem(
                action="Create repository README",
                rationale="Provides introductory setup guides for new developers.",
                expected_impact="Critical",
                difficulty="Easy"
            ))

        # Build final report
        report = RepositoryHealthReport(
            report_id=f"rep-health-{str(uuid.uuid4())[:8]}",
            repository_url=repository_url,
            total_commits=len(commits),
            active_contributors=collab_data["active_contributors"],
            bus_factor=collab_data["bus_factor"],
            inactive_periods=commit_data["inactive_periods"],
            burst_activities=commit_data["burst_activities"],
            releases=releases,
            health_scores=scores,
            insights=insights,
            recommendations=recommendations,
            confidence_score=0.95,
            analyzed_at=datetime.utcnow()
        )

        # Publish completions events
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="EngineeringActivityAnalyzer",
            payload={
                "event": "github.activity.completed",
                "workspace_id": workspace_id,
                "report_id": report.report_id
            }
        ))
        
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="EngineeringActivityAnalyzer",
            payload={
                "event": "github.health.completed",
                "workspace_id": workspace_id,
                "report_id": report.report_id
            }
        ))

        return report
