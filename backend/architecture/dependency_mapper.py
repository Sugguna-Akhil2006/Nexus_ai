"""Dependency mapper compiling component relations and Mermaid diagram strings."""

from __future__ import annotations

from typing import List

from backend.architecture.models import DependencyEdge, DependencyGraph, DependencyNode


class DependencyMapper:
    """Auto-generates subsystem interaction dependency maps and graphs."""

    @staticmethod
    def get_map() -> DependencyGraph:
        """Constructs components list, edges, and maps them to a Mermaid diagram string.

        Returns:
            DependencyGraph with Mermaid layouts.
        """
        nodes = [
            DependencyNode(node_id="runtime", label="Nexus Runtime", type="core"),
            DependencyNode(node_id="workflow", label="Workflow Engine", type="workflow"),
            DependencyNode(node_id="orchestrator", label="Execution Orchestrator", type="orchestrator"),
            DependencyNode(node_id="modules", label="Intelligence Modules", type="module"),
            DependencyNode(node_id="knowledge", label="Knowledge Fabric", type="knowledge"),
        ]

        edges = [
            DependencyEdge(from_node="runtime", to_node="workflow"),
            DependencyEdge(from_node="workflow", to_node="orchestrator"),
            DependencyEdge(from_node="orchestrator", to_node="modules"),
            DependencyEdge(from_node="modules", to_node="knowledge"),
        ]

        # Generate Mermaid string
        mermaid_lines = [
            "graph TD",
            "  runtime[Nexus Runtime] --> workflow[Workflow Engine]",
            "  workflow --> orchestrator[Execution Orchestrator]",
            "  orchestrator --> modules[Intelligence Modules]",
            "  modules --> knowledge[Knowledge Fabric]",
        ]

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            mermaid_diagram="\n".join(mermaid_lines),
        )
