"""Model comparator analyzing latency, cost, and accuracy across providers (Gemini, OpenAI, Anthropic, Ollama)."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.evaluation.models import ScenarioResult


class ModelComparator:
    """Compares metrics (accuracy, speed, cost) across multiple AI providers."""

    @staticmethod
    def compare_models(results: List[ScenarioResult]) -> List[Dict[str, Any]]:
        """Groups results by model name and calculates comparative analytics.

        Args:
            results: Results of benchmark runs.

        Returns:
            List of comparison dictionaries for each model configuration.
        """
        grouped: Dict[str, List[ScenarioResult]] = {}
        for r in results:
            grouped.setdefault(r.model_name, []).append(r)

        comparison = []
        for model, res_list in grouped.items():
            n = len(res_list)
            avg_acc = sum(r.metrics.accuracy for r in res_list) / n
            avg_lat = sum(r.metrics.latency_ms for r in res_list) / n
            avg_cost = sum(r.metrics.cost_usd for r in res_list) / n
            provider = res_list[0].provider_name

            comparison.append({
                "model_name": model,
                "provider_name": provider,
                "total_cases_run": n,
                "avg_accuracy": round(avg_acc, 4),
                "avg_latency_ms": round(avg_lat, 2),
                "avg_cost_usd": round(avg_cost, 6),
            })

        # Sort by accuracy descending, latency ascending
        comparison.sort(key=lambda x: (-x["avg_accuracy"], x["avg_latency_ms"]))
        return comparison
class WorkflowComparator:
    """Compares workflow performance across execution engine versions."""

    @staticmethod
    def compare_workflows(
        version_a_metrics: Dict[str, float],
        version_b_metrics: Dict[str, float],
    ) -> Dict[str, Any]:
        """Compares key metrics like overall latency, cost, and confidence between versions.

        Returns:
            Dict containing relative improvements.
        """
        lat_imp = version_a_metrics.get("latency_ms", 0.0) - version_b_metrics.get("latency_ms", 0.0)
        acc_imp = version_b_metrics.get("accuracy", 0.0) - version_a_metrics.get("accuracy", 0.0)

        return {
            "version_a_accuracy": version_a_metrics.get("accuracy", 0.0),
            "version_b_accuracy": version_b_metrics.get("accuracy", 0.0),
            "accuracy_improvement": round(acc_imp, 4),
            "latency_reduction_ms": round(lat_imp, 2),
            "better_version": "Version B" if acc_imp >= 0 else "Version A"
        }
