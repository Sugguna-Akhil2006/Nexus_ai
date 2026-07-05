"""Directed Knowledge Graph builder, path crawler, and query solver."""

from typing import List, Dict, Set, Tuple, Optional
from backend.intelligence.document.models import EntityNode, RelationshipEdge, DocumentGraph


class DocumentGraphBuilder:
    """Consolidates nodes and edges into directed graph maps, enabling structural walks."""

    def build_graph(self, nodes: List[EntityNode], edges: List[RelationshipEdge]) -> DocumentGraph:
        """Assembles distinct nodes and edges, pruning overlaps and duplicate keys.

        Args:
            nodes: Extracted entities list.
            edges: Relationship linkages list.

        Returns:
            DocumentGraph: Resolved graph model.
        """
        # Prune duplicate nodes (keep highest confidence)
        unique_nodes: Dict[str, EntityNode] = {}
        for n in nodes:
            n_key = n.name.lower()
            if n_key not in unique_nodes or n.confidence > unique_nodes[n_key].confidence:
                unique_nodes[n_key] = n

        # Prune duplicate edges
        unique_edges: Dict[Tuple[str, str, str], RelationshipEdge] = {}
        for e in edges:
            e_key = (e.source.lower(), e.target.lower(), e.relationship_type.lower())
            if e_key not in unique_edges or e.confidence > unique_edges[e_key].confidence:
                unique_edges[e_key] = e

        return DocumentGraph(
            nodes=list(unique_nodes.values()),
            edges=list(unique_edges.values())
        )

    def get_outgoing_connections(self, graph: DocumentGraph, node_name: str) -> List[RelationshipEdge]:
        """Lists edges leaving a node."""
        target_lbl = node_name.lower()
        return [e for e in graph.edges if e.source.lower() == target_lbl]

    def get_incoming_connections(self, graph: DocumentGraph, node_name: str) -> List[RelationshipEdge]:
        """Lists edges pointing to a node."""
        target_lbl = node_name.lower()
        return [e for e in graph.edges if e.target.lower() == target_lbl]

    def find_path(self, graph: DocumentGraph, start: str, end: str, max_depth: int = 4) -> List[str]:
        """Performs Depth First Search path matching between two nodes.

        Args:
            graph: Target Knowledge Graph.
            start: Start entity name.
            end: Target end entity name.
            max_depth: Maximum recursion depth.

        Returns:
            List[str]: List of nodes representing the path, empty if none exists.
        """
        start_lbl = start.lower()
        end_lbl = end.lower()
        
        # Build adjacency list
        adj: Dict[str, List[str]] = {}
        for e in graph.edges:
            s_node = e.source.lower()
            t_node = e.target.lower()
            if s_node not in adj:
                adj[s_node] = []
            adj[s_node].append(t_node)

        # Map display names
        disp_map = {n.name.lower(): n.name for n in graph.nodes}
        if start_lbl not in disp_map or end_lbl not in disp_map:
            return []

        visited = set()
        
        def dfs(curr: str, path: List[str], depth: int) -> Optional[List[str]]:
            if curr == end_lbl:
                return path + [disp_map[curr]]
            if depth >= max_depth or curr in visited:
                return None
            
            visited.add(curr)
            for neighbor in adj.get(curr, []):
                res = dfs(neighbor, path + [disp_map[curr]], depth + 1)
                if res:
                    return res
            visited.remove(curr)
            return None

        result = dfs(start_lbl, [], 0)
        return result or []
