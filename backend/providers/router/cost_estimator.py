"""Cost Estimator calculating price indices per model."""

from __future__ import annotations

from typing import Dict


class CostEstimator:
    """Estimates costs for LLM transactions based on catalog metadata."""

    def __init__(self) -> None:
        self._pricing: Dict[str, float] = {
            "gpt-4": 0.03,
            "claude-3-opus": 0.015,
            "gemini-1.5": 0.007,
            "phi3:mini": 0.000  # local model
        }

    def estimate_cost(self, model_id: str, tokens: int = 1000) -> float:
        """Returns estimated transactional cost in dollars."""
        rate = self._pricing.get(model_id.lower(), 0.002)
        return (tokens / 1000.0) * rate
