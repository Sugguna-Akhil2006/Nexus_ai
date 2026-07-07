"""Routing Policy defining priority weights for cost, quality, and latency."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyWeights:
    """Weights representing routing parameters priority (must sum to 1.0)."""

    cost_weight: float
    quality_weight: float
    latency_weight: float


class RoutingPolicyResolver:
    """Resolves cost/quality/latency weights based on target policy criteria."""

    def resolve_weights(self, preference: str) -> PolicyWeights:
        """Resolves weights coefficients."""
        pref = preference.lower()
        if pref == "cost":
            return PolicyWeights(cost_weight=0.8, quality_weight=0.1, latency_weight=0.1)
        elif pref == "quality":
            return PolicyWeights(cost_weight=0.01, quality_weight=0.98, latency_weight=0.01)
        elif pref == "latency":
            return PolicyWeights(cost_weight=0.01, quality_weight=0.01, latency_weight=0.98)
        else:  # balanced
            return PolicyWeights(cost_weight=0.33, quality_weight=0.33, latency_weight=0.34)

