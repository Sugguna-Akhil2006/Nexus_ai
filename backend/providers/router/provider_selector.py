"""Provider Selector scoring models dynamically based on weights."""

from __future__ import annotations

from typing import List

from backend.platform.models import ModelProfile
from backend.providers.router.routing_policy import PolicyWeights
from backend.providers.router.cost_estimator import CostEstimator
from backend.providers.router.latency_predictor import LatencyPredictor
from backend.providers.router.quality_ranker import QualityRanker


class ProviderSelector:
    """Selects optimal model by calculating weighted score combinations."""

    def __init__(self) -> None:
        self.cost_estimator = CostEstimator()
        self.latency_predictor = LatencyPredictor()
        self.quality_ranker = QualityRanker()

    def select_best_model(self, eligible_models: List[ModelProfile], weights: PolicyWeights) -> ModelProfile:
        """Calculates score per candidate and returns the highest scoring model."""
        if not eligible_models:
            raise ValueError("No eligible models to select from.")

        best_model = eligible_models[0]
        best_score = -999.0

        for m in eligible_models:
            # Normalize params:
            # cost (lower is better, e.g. phi3=0.0, gpt4=0.03) -> score
            cost = self.cost_estimator.estimate_cost(m.model_id)
            cost_score = 1.0 - (cost / 0.05)  # cap at 5 cents

            # latency (lower is better) -> score
            latency = self.latency_predictor.predict_latency_ms(m.model_id)
            latency_score = 1.0 - (latency / 1000.0)  # cap at 1 second

            # quality (higher is better) -> score
            quality = self.quality_ranker.get_quality_score(m.model_id)
            quality_score = quality / 100.0

            # Weighted sum
            score = (
                (weights.cost_weight * cost_score) +
                (weights.latency_weight * latency_score) +
                (weights.quality_weight * quality_score)
            )

            if score > best_score:
                best_score = score
                best_model = m

        return best_model
