"""Derives and accumulates estimated costs from token usage with configurable pricing."""

import threading
from collections import defaultdict
from typing import Any, Dict

# Default per-token pricing in USD (can be overridden at construction)
_DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "default": {"input": 0.000001, "output": 0.000002},
}


class CostTracker:
    """Computes and aggregates estimated inference costs by workspace and model."""

    def __init__(self, pricing: Dict[str, Dict[str, float]] | None = None) -> None:
        self._lock = threading.Lock()
        self._pricing: Dict[str, Dict[str, float]] = {**_DEFAULT_PRICING, **(pricing or {})}
        # workspace_id → total cost USD
        self._workspace_costs: Dict[str, float] = defaultdict(float)
        # model → total cost USD
        self._model_costs: Dict[str, float] = defaultdict(float)

    def _price_for(self, model: str) -> Dict[str, float]:
        """Returns the pricing table for a model, falling back to ``default``."""
        return self._pricing.get(model, self._pricing["default"])

    def record_cost(
        self,
        workspace_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> float:
        """Calculates and records the estimated cost for a single invocation.

        Args:
            workspace_id: Originating workspace.
            model: Model identifier used for pricing lookup.
            tokens_in: Prompt token count.
            tokens_out: Completion token count.

        Returns:
            The estimated cost in USD for this invocation.
        """
        prices = self._price_for(model)
        cost = (tokens_in * prices["input"]) + (tokens_out * prices["output"])
        with self._lock:
            self._workspace_costs[workspace_id] += cost
            self._model_costs[model] += cost
        return round(cost, 8)

    def get_workspace_cost(self, workspace_id: str) -> float:
        """Returns accumulated cost for a workspace in USD."""
        with self._lock:
            return round(self._workspace_costs.get(workspace_id, 0.0), 6)

    def get_cost_report(self) -> Dict[str, Any]:
        """Returns a full cost breakdown by workspace and model.

        Returns:
            Dict with ``by_workspace`` and ``by_model`` keys.
        """
        with self._lock:
            return {
                "by_workspace": {k: round(v, 6) for k, v in self._workspace_costs.items()},
                "by_model": {k: round(v, 6) for k, v in self._model_costs.items()},
                "total_usd": round(sum(self._workspace_costs.values()), 6),
            }
