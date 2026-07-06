"""Implements querying, path search (BFS), similarity lookups, and subgraphs extraction."""

import collections
from typing import Dict, List, Set, Tuple, Optional
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.knowledge.graph_storage import GraphStorage


class GraphSearcher:
    """Provides pathfinder utilities and neighborhood analysis queries over GraphStorage."""

    def __init__(self, storage: GraphStorage) -> None:
        self.storage = storage

    def search_entities(
        self,
        workspace_id: str,
        query: Optional[str] = None,
        label: Optional[EntityType] = None
    ) -> List[EntityNode]:
        """Filters nodes by text match and/or label type."""
        nodes = self.storage.list_nodes(workspace_id)
        results = []
        for n in nodes:
            if label and n.label != label:
                continue
            if query:
                q_lower = query.lower()
                if q_lower not in n.name.lower() and not any(q_lower in str(v).lower() for v in n.properties.values()):
                    continue
            results.append(n)
        return results

    def search_relationships(
        self,
        workspace_id: str,
        rel_type: Optional[RelationshipType] = None
    ) -> List[Relationship]:
        """Filters relationships by relationship type."""
        rels = self.storage.list_relationships(workspace_id)
        if rel_type:
            return [r for r in rels if r.relationship_type == rel_type]
        return rels

    def find_paths(
        self,
        workspace_id: str,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 3
    ) -> List[List[Relationship]]:
        """Finds all directed paths from start_node_id to end_node_id up to max_depth using BFS.

        Returns:
            List[List[Relationship]]: List of paths, where each path is a list of Relationship edges.
        """
        # Fetch relationships to build adjacency list
        all_rels = self.storage.list_relationships(workspace_id)
        adj: Dict[str, List[Relationship]] = collections.defaultdict(list)
        for r in all_rels:
            adj[r.source_id].append(r)

        paths: List[List[Relationship]] = []
        # Queue item: (current_node, current_path)
        queue = collections.deque([(start_node_id, [])])

        while queue:
            curr_node, curr_path = queue.popleft()
            
            if curr_node == end_node_id and curr_path:
                paths.append(curr_path)
                continue
                
            if len(curr_path) >= max_depth:
                continue

            # Prevent cycles
            visited_nodes = {r.source_id for r in curr_path} | {r.target_id for r in curr_path}
            
            for edge in adj[curr_node]:
                # If target not already visited in this path
                if edge.target_id not in visited_nodes or edge.target_id == end_node_id:
                    queue.append((edge.target_id, curr_path + [edge]))

        return paths

    def get_neighborhood(
        self,
        workspace_id: str,
        node_id: str,
        depth: int = 1
    ) -> Tuple[List[EntityNode], List[Relationship]]:
        """Retrieves nodes and edges within a specified hop distance of the source node."""
        all_nodes = {n.node_id: n for n in self.storage.list_nodes(workspace_id)}
        all_rels = self.storage.list_relationships(workspace_id)

        # Adjacency maps for undirected-like neighborhood traversal
        neighbors_map = collections.defaultdict(list)
        for r in all_rels:
            neighbors_map[r.source_id].append(r)
            neighbors_map[r.target_id].append(r)

        visited_nodes: Set[str] = {node_id}
        visited_rels: Set[str] = set()

        current_layer = {node_id}
        for _ in range(depth):
            next_layer = set()
            for curr in current_layer:
                for rel in neighbors_map[curr]:
                    visited_rels.add(rel.relationship_id)
                    # Add opposite node
                    other = rel.target_id if rel.source_id == curr else rel.source_id
                    if other not in visited_nodes:
                        visited_nodes.add(other)
                        next_layer.add(other)
            current_layer = next_layer

        nodes_list = [all_nodes[nid] for nid in visited_nodes if nid in all_nodes]
        rels_map = {r.relationship_id: r for r in all_rels}
        rels_list = [rels_map[rid] for rid in visited_rels if rid in rels_map]

        return nodes_list, rels_list

    def search_similar_nodes(
        self,
        workspace_id: str,
        target_node_id: str,
        limit: int = 5
    ) -> List[Tuple[EntityNode, float]]:
        """Finds other nodes in the graph sharing similar property keys or outgoing neighbors.

        Uses Jaccard overlap on outgoing neighbor target IDs.
        """
        all_nodes = self.storage.list_nodes(workspace_id)
        target_node = next((n for n in all_nodes if n.node_id == target_node_id), None)
        if not target_node:
            return []

        all_rels = self.storage.list_relationships(workspace_id)
        
        # Outgoing targets for each node
        outgoing_targets: Dict[str, Set[str]] = collections.defaultdict(set)
        for r in all_rels:
            outgoing_targets[r.source_id].add(r.target_id)

        target_set = outgoing_targets[target_node_id]
        scored_nodes = []

        for node in all_nodes:
            if node.node_id == target_node_id:
                continue
            
            node_set = outgoing_targets[node.node_id]
            
            # Label match boost
            label_boost = 0.2 if node.label == target_node.label else 0.0
            
            # Compute Jaccard on outgoing connections
            intersection = len(target_set & node_set)
            union = len(target_set | node_set)
            jaccard = (intersection / union) if union > 0 else 0.0
            
            score = jaccard + label_boost
            if score > 0.0:
                scored_nodes.append((node, round(score, 2)))

        scored_nodes.sort(key=lambda x: x[1], reverse=True)
        return scored_nodes[:limit]

    def extract_subgraph(
        self,
        workspace_id: str,
        node_ids: List[str]
    ) -> Tuple[List[EntityNode], List[Relationship]]:
        """Extracts the sub-network consisting of the specified node_ids and their inter-connecting edges."""
        all_nodes = {n.node_id: n for n in self.storage.list_nodes(workspace_id)}
        all_rels = self.storage.list_relationships(workspace_id)

        target_set = set(node_ids)
        nodes_list = [all_nodes[nid] for nid in target_set if nid in all_nodes]
        
        rels_list = []
        for r in all_rels:
            if r.source_id in target_set and r.target_id in target_set:
                rels_list.append(r)
                
        return nodes_list, rels_list
