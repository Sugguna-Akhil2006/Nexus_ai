"""Leaderboard tracking and rankings accumulator for AI models and providers."""

from __future__ import annotations

import threading
from typing import Dict, List

from backend.evaluation.models import ModelRank, ScenarioResult


class Leaderboard:
    """Thread-safe catalog of model benchmarks rankings and scorecards."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._ranks: List[ModelRank] = []

    def update_rankings(self, results: List[ScenarioResult]) -> List[ModelRank]:
        """Calculates rankings based on scenario output metrics.

        Args:
            results: Combined benchmark execution scenario results.

        Returns:
            Sorted List of ModelRank standings.
        """
        with self._lock:
            # Group by model
            grouped: Dict[str, List[ScenarioResult]] = {}
            for r in results:
                grouped.setdefault(r.model_name, []).append(r)

            ranks = []
            for model, res_list in grouped.items():
                n = len(res_list)
                avg_acc = sum(r.metrics.accuracy for r in res_list) / n
                avg_lat = sum(r.metrics.latency_ms for r in res_list) / n
                avg_cost = sum(r.metrics.cost_usd for r in res_list) / n
                provider = res_list[0].provider_name

                # Score formula: accuracy weight 70%, latency penalty 20%, cost penalty 10%
                latency_score = max(0.0, 1.0 - (avg_lat / 2000.0))  # normalize latency
                overall = (avg_acc * 0.7) + (latency_score * 0.3)

                ranks.append(
                    ModelRank(
                        model_name=model,
                        provider_name=provider,
                        avg_accuracy=avg_acc,
                        avg_latency_ms=avg_lat,
                        avg_cost_usd=avg_cost,
                        overall_score=round(overall * 100, 2),
                    )
                )

            # Sort by overall score descending
            ranks.sort(key=lambda x: x.overall_score, reverse=True)

            # Assign rank position indexes
            for idx, r in enumerate(ranks):
                r.rank = idx + 1

            self._ranks = ranks
            return list(self._ranks)

    def get_rankings(self) -> List[ModelRank]:
        """Returns the current leaderboard rankings."""
        with self._lock:
            return list(self._ranks)
