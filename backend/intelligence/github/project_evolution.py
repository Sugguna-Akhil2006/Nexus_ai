"""Evaluates codebase timeline growth, refactoring trends, and dependency growth."""

from typing import List, Dict, Any


class ProjectEvolutionAnalyzer:
    """Analyzes commit message metadata for refactoring, tech additions, and structural drift."""

    def analyze_evolution(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Scans commit list messages to build evolutionary trends.

        Args:
            commits: List of commit details.

        Returns:
            Dict[str, Any]: Evolution stats.
        """
        refactor_count = 0
        dependency_count = 0
        architecture_count = 0

        for c in commits:
            msg = str(c["message"]).lower()
            if "refactor" in msg or "cleanup" in msg or "reorganize" in msg or "redesign" in msg:
                refactor_count += 1
            if "dependency" in msg or "package" in msg or "import" in msg or "upgrade" in msg:
                dependency_count += 1
            if "architecture" in msg or "layer" in msg or "modular" in msg or "hexagonal" in msg:
                architecture_count += 1

        total = len(commits)
        refactor_pct = (refactor_count / total * 100.0) if total > 0 else 0.0

        return {
            "refactoring_commits": refactor_count,
            "refactoring_percentage": round(refactor_pct, 1),
            "dependency_changes": dependency_count,
            "architecture_changes": architecture_count
        }
