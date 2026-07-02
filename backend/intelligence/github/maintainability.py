"""Calculates project code maintainability indexes and extension ratings."""

from typing import List
from backend.intelligence.github.repository import GitRepositoryReader


class MaintainabilityCalculator:
    """Calculates overall modularity and maintainability scores."""

    def calculate_maintainability(
        self,
        complexity_score: float,
        anti_patterns: List[str]
    ) -> float:
        """Heuristically computes standard Halstead-like maintainability index.

        Args:
            complexity_score: Cyclomatic complexity estimate.
            anti_patterns: Discovered anti-pattern structures.

        Returns:
            float: Score from 0 to 100.
        """
        # Base index of 100
        score = 100.0
        
        # Deduct based on complexity
        # Complexity of 0 -> 0 deduction. Complexity of 100 -> 40 points deduction.
        score -= (complexity_score / 100.0) * 40.0
        
        # Deduct based on anti-patterns count
        # 10 points deduction per anti-pattern found, up to 40 max
        score -= min(40.0, len(anti_patterns) * 10.0)
        
        return max(0.0, round(score, 1))
