"""Analyzes commit messages, frequency, inactive gaps, and conventional formats."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.intelligence.github.models import InactivePeriod, BurstActivity


class CommitAnalyzer:
    """Analyzes repository commit history datasets for velocity, gaps, and quality."""

    def analyze_commits(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs metric calculations over commit metadata history.

        Args:
            commits: List of commit metadata objects.

        Returns:
            Dict[str, Any]: Calculated metrics.
        """
        if not commits:
            return {
                "total_commits": 0,
                "conventional_percent": 100.0,
                "inactive_periods": [],
                "burst_activities": [],
                "active_days_count": 0
            }

        # Sort commits chronologically
        sorted_commits = sorted(commits, key=lambda c: c["timestamp"])
        
        # 1. Conventional Commits validation
        conv_prefixes = ("feat:", "fix:", "chore:", "docs:", "style:", "refactor:", "perf:", "test:", "ci:")
        conv_count = sum(1 for c in sorted_commits if str(c["message"]).lower().startswith(conv_prefixes))
        conv_percent = (conv_count / len(sorted_commits)) * 100.0

        # 2. Inactive Periods (> 14 days without commits)
        inactive_periods = []
        for i in range(1, len(sorted_commits)):
            prev_time = sorted_commits[i-1]["timestamp"]
            curr_time = sorted_commits[i]["timestamp"]
            delta = curr_time - prev_time
            if delta.days > 14:
                inactive_periods.append(InactivePeriod(
                    start_date=prev_time,
                    end_date=curr_time,
                    duration_days=delta.days
                ))

        # 3. Burst Activities (multiple commits in a single day)
        commits_by_day = {}
        for c in sorted_commits:
            day_str = c["timestamp"].date()
            commits_by_day[day_str] = commits_by_day.get(day_str, 0) + 1

        burst_activities = []
        for day, count in commits_by_day.items():
            if count >= 5:  # Define a burst as 5 or more commits in a single day
                burst_activities.append(BurstActivity(
                    date=datetime.combine(day, datetime.min.time()),
                    commit_count=count,
                    impact_description=f"High development velocity period with {count} commit pushes."
                ))

        return {
            "total_commits": len(commits),
            "conventional_percent": round(conv_percent, 1),
            "inactive_periods": inactive_periods,
            "burst_activities": burst_activities,
            "active_days_count": len(commits_by_day)
        }
