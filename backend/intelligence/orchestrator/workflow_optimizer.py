"""Workflow optimizer adjusting execution graphs according to policy constraints."""

from __future__ import annotations

import logging

from backend.intelligence.orchestrator.execution_policy import PolicyType
from backend.intelligence.orchestrator.models import OrchestrationPlan

logger = logging.getLogger("nexus.orchestrator.optimizer")


class WorkflowOptimizer:
    """Optimizes the execution plan nodes and graph based on the policy type."""

    @staticmethod
    def optimize(plan: OrchestrationPlan) -> OrchestrationPlan:
        """Applies optimizations to the plan's graph.

        Args:
            plan: Input orchestration plan.

        Returns:
            Optimized OrchestrationPlan.
        """
        policy = plan.policy
        graph = plan.graph

        if policy.policy_type == PolicyType.FASTEST:
            # 1. Limit concurrency to policy limit
            policy.max_concurrency = min(policy.max_concurrency, 6)
            # 2. Skip slower heavy modules if optional (e.g., skip 'research' if other nodes exist)
            if len(graph.nodes) > 1 and "node-research" in graph.nodes:
                logger.info("Fastest policy active: Pruning research node to optimize speed.")
                graph.nodes.pop("node-research")
                # Remove edges
                graph.edges = [e for e in graph.edges if e[0] != "node-research" and e[1] != "node-research"]

        elif policy.policy_type == PolicyType.LOWEST_COST:
            # 1. Prefer cache
            policy.cache_preferred = True
            # 2. Prune expensive nodes (e.g. career recommenders / professional agents if they exceed limits)
            if len(graph.nodes) > 1 and "node-professional" in graph.nodes:
                logger.info("Lowest Cost policy active: Pruning professional node.")
                graph.nodes.pop("node-professional")
                graph.edges = [e for e in graph.edges if e[0] != "node-professional" and e[1] != "node-professional"]

        elif policy.policy_type == PolicyType.HIGHEST_QUALITY:
            # 1. Disable cache to get fresh inference
            policy.cache_preferred = False
            # 2. Increase concurrency and set high timeouts
            policy.max_concurrency = max(policy.max_concurrency, 8)
            policy.timeout_seconds = max(policy.timeout_seconds, 120.0)

        return plan
