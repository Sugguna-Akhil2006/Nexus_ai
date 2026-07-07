"""Cost Manager managing token pricing calculation checks."""

from __future__ import annotations

from typing import Dict


class CostManager:
    """Estimates costs for model transactions."""

    def __init__(self) -> None:
        # Default price per 1k input tokens
        self._pricing: Dict[str, float] = {
            "gpt-4": 0.03,
            "claude-3-opus": 0.015,
            "gemini-1.5": 0.007,
            "phi3:mini": 0.000  # local Ollama model is free
        }

    def calculate_cost(self, model_id: str, tokens: int) -> float:
        """Returns cost in dollars."""
        rate = self._pricing.get(model_id.lower(), 0.0015)
        return (tokens / 1000.0) * rate
