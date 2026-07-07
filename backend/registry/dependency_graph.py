"""Dependency graph showing capability mappings and relationship traces."""

from __future__ import annotations

from typing import Dict, List, Set

from backend.registry.capability_registry import CapabilityRegistry


class DependencyGraph:
    """Generates and traces the AI capability dependency relationships structure."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def build_graph(self) -> Dict[str, List[str]]:
        """Builds an adjacency list representation of all capability dependencies."""
        caps = self.registry.list_capabilities()
        graph = {}
        for c in caps:
            graph[c.capability_id] = c.dependencies
        return graph

    def get_downstream_dependencies(self, capability_id: str) -> List[str]:
        """Resolves transitive downstream dependencies (BFS/DFS traversal)."""
        graph = self.build_graph()
        if capability_id not in graph:
            return []

        visited: Set[str] = set()
        queue = list(graph[capability_id])
        
        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                # Queue nested dependency children
                if node in graph:
                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            queue.append(neighbor)

        return list(visited)

    def generate_mermaid_diagram(self) -> str:
        """Helper to generate a Mermaid flow diagram representing the dependency tree."""
        graph = self.build_graph()
        lines = ["graph TD"]
        for parent, children in graph.items():
            for child in children:
                lines.append(f"    {parent} --> {child}")
        return "\n".join(lines)
