"""Workflow planner mapping selected modules into a directed acyclic execution graph."""

from __future__ import annotations

from typing import Dict, List

from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.orchestrator.execution_policy import ExecutionPolicy
from backend.intelligence.orchestrator.models import ExecutionGraph, ExecutionNode, OrchestrationPlan


class WorkflowPlanner:
    """Constructs the ExecutionGraph and configures nodes based on query context."""

    def __init__(self) -> None:
        self._registry = IntelligenceRegistry()

        # Hardcoded dependency constraints as specified in contracts
        # key depends on value list
        self._DEPENDENCY_RULES = {
            "knowledge": ["resume", "github", "document"],
            "professional": ["knowledge"],
            "composition": ["professional"],
        }

    def plan(
        self,
        modules: List[str],
        policy: ExecutionPolicy,
    ) -> OrchestrationPlan:
        """Generates an OrchestrationPlan with nodes and dependency relationships.

        Args:
            modules: Target module names to execute.
            policy: Selected execution policy.

        Returns:
            OrchestrationPlan detailing the execution DAG.
        """
        nodes: Dict[str, ExecutionNode] = {}
        edges: List[tuple[str, str]] = []

        # 1. Create nodes for all participating modules
        for mod_name in modules:
            node_id = f"node-{mod_name}"
            # Resolve capability
            capability = "GENERAL_INTELLIGENCE"
            try:
                mod = self._registry.get_module(mod_name)
                if mod.capabilities:
                    capability = list(mod.capabilities)[0]
            except Exception:
                pass

            nodes[node_id] = ExecutionNode(
                node_id=node_id,
                module_name=mod_name,
                capability=capability,
            )

        # 2. Establish dependencies based on rules
        for node_id, node in nodes.items():
            deps = self._DEPENDENCY_RULES.get(node.module_name, [])
            for dep_name in deps:
                dep_node_id = f"node-{dep_name}"
                if dep_node_id in nodes:
                    node.dependencies.append(dep_node_id)
                    edges.append((dep_node_id, node_id))

        graph = ExecutionGraph(
            nodes=nodes,
            edges=edges,
        )

        return OrchestrationPlan(
            graph=graph,
            policy=policy,
        )
