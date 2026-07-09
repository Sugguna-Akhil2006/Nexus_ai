"""Dependency resolver executing topological sorts and cycle detection on execution graphs."""

from __future__ import annotations

from typing import Dict, List, Set

from backend.intelligence.orchestrator.models import ExecutionGraph, ExecutionNode


class DependencyResolver:
    """Performs topological sorting and validates DAG traits (cycle detection)."""

    @classmethod
    def resolve(cls, graph: ExecutionGraph) -> List[List[str]]:
        """Splits the graph nodes into sequential batches that can be run concurrently.

        Each batch contains nodes whose dependencies are already completed.

        Args:
            graph: The execution graph to sort.

        Returns:
            List of batches, where each batch is a list of node_ids.

        Raises:
            ValueError: If a circular dependency is detected.
        """
        # Cycle detection check
        cls.detect_cycles(graph)

        in_degree: Dict[str, int] = {}
        adjacency: Dict[str, List[str]] = {nid: [] for nid in graph.nodes}

        for nid, node in graph.nodes.items():
            in_degree[nid] = len(node.dependencies)
            for dep in node.dependencies:
                if dep in adjacency:
                    adjacency[dep].append(nid)

        batches: List[List[str]] = []
        visited: Set[str] = set()

        while len(visited) < len(graph.nodes):
            current_batch = [
                nid for nid, deg in in_degree.items()
                if deg == 0 and nid not in visited
            ]

            if not current_batch:
                # Should not happen since detect_cycles passed, but acts as fallback
                raise ValueError("Circular dependency detected during batch extraction.")

            batches.append(current_batch)
            for nid in current_batch:
                visited.add(nid)
                for neighbor in adjacency[nid]:
                    in_degree[neighbor] -= 1

        return batches

    @classmethod
    def detect_cycles(cls, graph: ExecutionGraph) -> None:
        """Runs a depth-first search (DFS) to verify the graph is acyclic.

        Raises:
            ValueError: If a cycle is present.
        """
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node_id: str) -> bool:
            visited.add(node_id)
            rec_stack.add(node_id)

            node = graph.nodes.get(node_id)
            if node:
                for dep in node.dependencies:
                    if dep not in visited:
                        if dfs(dep):
                            return True
                    elif dep in rec_stack:
                        return True

            rec_stack.remove(node_id)
            return False

        for node_id in graph.nodes:
            if node_id not in visited:
                if dfs(node_id):
                    raise ValueError(f"Circular dependency detected involving node: {node_id}")
