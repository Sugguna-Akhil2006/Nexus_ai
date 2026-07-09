"""Workflow comparator analyzing workflow execution structures and pipeline version variations."""

from __future__ import annotations

from typing import Any, Dict


class WorkflowComparator:
    """Compares pipeline topologies, latency logs, and cost structures between different run versions."""

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
