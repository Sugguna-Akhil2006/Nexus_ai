"""Evaluates contributors distributions, merge activities, and estimates Bus Factors."""

from typing import List, Dict, Any


class CollaborationEvaluator:
    """Evaluates project contributor distributions and Bus Factor metrics."""

    def evaluate_collaboration(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs calculations on authors across commits list.

        Args:
            commits: List of commit dictionary datasets.

        Returns:
            Dict[str, Any]: Collaboration statistics.
        """
        if not commits:
            return {
                "active_contributors": 0,
                "bus_factor": 1,
                "author_distribution": {}
            }

        # Calculate commit distribution by author
        author_commits = {}
        for c in commits:
            author = c["author"] or "Unknown"
            author_commits[author] = author_commits.get(author, 0) + 1

        total_commits = len(commits)
        sorted_distribution = sorted(author_commits.items(), key=lambda x: x[1], reverse=True)

        # Bus Factor calculation: minimum number of authors who represent > 80% of commits
        cumulative_commits = 0
        bus_factor = 0
        for author, count in sorted_distribution:
            cumulative_commits += count
            bus_factor += 1
            if cumulative_commits >= total_commits * 0.8:
                break

        return {
            "active_contributors": len(author_commits),
            "bus_factor": max(1, bus_factor),
            "author_distribution": author_commits
        }
