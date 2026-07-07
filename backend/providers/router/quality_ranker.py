"""Quality Ranker rating accuracy indices per model."""

from __future__ import annotations

from typing import Dict


class QualityRanker:
    """Ranks models based on performance benchmarks indices."""

    def __init__(self) -> None:
        self._quality_scores: Dict[str, int] = {
            "gpt-4": 95,
            "claude-3-opus": 93,
            "gemini-1.5": 88,
            "phi3:mini": 72
        }

    def get_quality_score(self, model_id: str) -> int:
        """Returns quality index (1-100)."""
        return self._quality_scores.get(model_id.lower(), 70)
