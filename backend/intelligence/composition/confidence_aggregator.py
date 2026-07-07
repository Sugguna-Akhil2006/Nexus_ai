"""Confidence aggregator — combines per-module confidence scores into one value."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.intelligence.composition.models import AggregatedConfidence, ConfidenceStrategy
from backend.intelligence.contracts.response_models import IntelligenceResponse


class ConfidenceAggregator:
    """Aggregates confidence scores from multiple intelligence modules.

    Supported strategies:
    - AVERAGE: Arithmetic mean of all module confidences.
    - WEIGHTED_AVERAGE: Weighted mean where weights are proportional to token output.
    - MIN: Lowest module confidence (conservative estimate).
    - MAX: Highest module confidence (optimistic estimate).
    """

    @staticmethod
    def aggregate(
        responses: List[IntelligenceResponse],
        strategy: ConfidenceStrategy = ConfidenceStrategy.WEIGHTED_AVERAGE,
        manual_weights: Optional[Dict[str, float]] = None,
    ) -> AggregatedConfidence:
        """Computes an aggregated confidence value.

        Args:
            responses: Module responses to aggregate.
            strategy:  Aggregation algorithm. Defaults to WEIGHTED_AVERAGE.
            manual_weights: Optional mapping of module → weight. Used only when
                            ``strategy == WEIGHTED_AVERAGE``.  If omitted, weights
                            are derived from ``execution_metrics.tokens_out``.

        Returns:
            ``AggregatedConfidence`` with overall score and per-module breakdown.
        """
        if not responses:
            return AggregatedConfidence(
                overall=0.0,
                strategy=strategy,
            )

        per_module: Dict[str, float] = {r.module: r.confidence for r in responses}
        confidences = list(per_module.values())

        if strategy == ConfidenceStrategy.AVERAGE:
            overall = sum(confidences) / len(confidences)
            weights: Dict[str, float] = {}

        elif strategy == ConfidenceStrategy.MIN:
            overall = min(confidences)
            weights = {}

        elif strategy == ConfidenceStrategy.MAX:
            overall = max(confidences)
            weights = {}

        else:  # WEIGHTED_AVERAGE
            weights = ConfidenceAggregator._derive_weights(responses, manual_weights)
            overall = sum(
                per_module.get(mod, 0.0) * w for mod, w in weights.items()
            )

        return AggregatedConfidence(
            overall=round(min(max(overall, 0.0), 1.0), 4),
            strategy=strategy,
            per_module=per_module,
            weights=weights,
            min_confidence=min(confidences),
            max_confidence=max(confidences),
        )

    @staticmethod
    def _derive_weights(
        responses: List[IntelligenceResponse],
        manual_weights: Optional[Dict[str, float]],
    ) -> Dict[str, float]:
        """Derives per-module weights, falling back to uniform if all zero."""
        if manual_weights:
            total = sum(manual_weights.values())
            if total > 0:
                return {k: v / total for k, v in manual_weights.items()}

        # Weight proportional to tokens_out (proxy for output depth)
        raw: Dict[str, float] = {
            r.module: float(r.execution_metrics.tokens_out or 1)
            for r in responses
        }
        total = sum(raw.values())
        if total == 0:
            n = len(responses)
            return {r.module: 1.0 / n for r in responses}
        return {mod: val / total for mod, val in raw.items()}
