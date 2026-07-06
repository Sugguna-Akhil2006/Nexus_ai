"""Calculates aggregate confidence scores and propagates edge path weights."""

from typing import List


class ConfidenceEngine:
    """Computes combined confidence metrics using probabilistic formulations."""

    @staticmethod
    def aggregate_confidence(score1: float, score2: float) -> float:
        """Computes aggregated confidence score when merging duplicate elements.

        Uses the independent probabilistic union equation:
        P(A U B) = 1.0 - (1.0 - P(A)) * (1.0 - P(B))

        Caps the output value at 0.99.
        """
        # Ensure values are within range 0.0 - 1.0
        s1 = max(0.0, min(1.0, score1))
        s2 = max(0.0, min(1.0, score2))
        
        combined = 1.0 - (1.0 - s1) * (1.0 - s2)
        return round(min(0.99, combined), 2)

    @staticmethod
    def propagate_path_confidence(scores: List[float]) -> float:
        """Computes path traversal confidence by multiplying individual edge weights.

        Returns 0.0 if scores is empty.
        """
        if not scores:
            return 0.0

        product = 1.0
        for s in scores:
            val = max(0.0, min(1.0, s))
            product *= val
        
        return round(product, 2)
