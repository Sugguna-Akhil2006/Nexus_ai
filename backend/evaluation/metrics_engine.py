"""Metrics engine scoring accuracy, completeness, latency, cost, and consistency averages."""

from __future__ import annotations

from typing import List

from backend.evaluation.models import EvalMetrics, ScenarioResult


class MetricsEngine:
    """Calculates aggregates and averages of scored parameters across test runs."""

    @staticmethod
    def calculate_averages(results: List[ScenarioResult]) -> EvalMetrics:
        """Averages scores across all provided ScenarioResults.

        Args:
            results: Results of scenarios run.

        Returns:
            EvalMetrics containing averages.
        """
        n_results = len(results)
        if n_results == 0:
            return EvalMetrics()

        accuracy_sum = 0.0
        completeness_sum = 0.0
        hallucination_sum = 0.0
        citation_sum = 0.0
        latency_sum = 0.0
        cost_sum = 0.0
        confidence_sum = 0.0
        consistency_sum = 0.0

        for r in results:
            m = r.metrics
            accuracy_sum += m.accuracy
            completeness_sum += m.completeness
            hallucination_sum += m.hallucination_rate
            citation_sum += m.citation_quality
            latency_sum += m.latency_ms
            cost_sum += m.cost_usd
            confidence_sum += m.confidence
            consistency_sum += m.consistency

        return EvalMetrics(
            accuracy=round(accuracy_sum / n_results, 4),
            completeness=round(completeness_sum / n_results, 4),
            hallucination_rate=round(hallucination_sum / n_results, 4),
            citation_quality=round(citation_sum / n_results, 4),
            latency_ms=round(latency_sum / n_results, 2),
            cost_usd=round(cost_sum / n_results, 6),
            confidence=round(confidence_sum / n_results, 4),
            consistency=round(consistency_sum / n_results, 4),
        )
