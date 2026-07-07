"""Prompt evaluator running A/B testing and scanning for regression between versions."""

from __future__ import annotations

from typing import Any, Dict, List


class PromptEvaluator:
    """Evaluates prompt performance variations and detects quality regressions."""

    @staticmethod
    def compare_prompts(
        results_a: List[Dict[str, Any]],
        results_b: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compares Prompt A to Prompt B outputs and metrics.

        Args:
            results_a: List of outcome dicts for Prompt A.
            results_b: List of outcome dicts for Prompt B.

        Returns:
            Dict compiling comparative improvements and regression flags.
        """
        avg_acc_a = sum(r.get("accuracy", 0.90) for r in results_a) / len(results_a) if results_a else 0.0
        avg_acc_b = sum(r.get("accuracy", 0.90) for r in results_b) / len(results_b) if results_b else 0.0

        improvement = avg_acc_b - avg_acc_a
        regression = improvement < -0.02  # significant drop

        return {
            "prompt_a_avg_accuracy": round(avg_acc_a, 4),
            "prompt_b_avg_accuracy": round(avg_acc_b, 4),
            "accuracy_improvement": round(improvement, 4),
            "regression_detected": regression,
            "comparison_summary": "Prompt B outperformed Prompt A" if improvement > 0 else "Prompt A outperformed Prompt B",
        }
