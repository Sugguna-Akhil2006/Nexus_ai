"""Orchestrates high-level logical inferences, identifying professional expertise alignment and technology stacks."""

import collections
from typing import Dict, List, Any
from backend.intelligence.knowledge.graph_storage import GraphStorage
from backend.intelligence.knowledge.inference import SemanticInferrer
from backend.intelligence.knowledge.models import EntityType, RelationshipType


class SemanticReasoner:
    """Orchestrator for semantic deduction, skill clustering, and profile validation checks."""

    def __init__(self, storage: GraphStorage) -> None:
        self.storage = storage
        self.inferrer = SemanticInferrer()

    def execute_reasoning(self, workspace_id: str) -> Dict[str, Any]:
        """Runs rule inferences, stashes inferred relationships, and isolates expertise gaps."""
        # 1. Infer new relationships
        new_rels = self.inferrer.infer_relationships(workspace_id, self.storage)
        
        # Persist new relationships
        for rel in new_rels:
            self.storage.upsert_relationship(workspace_id, rel)

        # 2. Identify knowledge gaps
        gaps = self.inferrer.identify_knowledge_gaps(workspace_id, self.storage)

        # 3. Analyze technology clusters (co-occurrence of technologies in projects/repositories)
        co_occurrences = self._compute_tech_clusters(workspace_id)

        # 4. Infer technology stack groupings
        tech_stacks = self._infer_tech_stacks(workspace_id)

        return {
            "inferred_relationships_count": len(new_rels),
            "knowledge_gaps": gaps,
            "tech_co_occurrence_clusters": co_occurrences,
            "technology_stacks": tech_stacks
        }

    def _compute_tech_clusters(self, workspace_id: str) -> Dict[str, List[str]]:
        """Identifies clusters of skills/technologies that are frequently co-used in projects."""
        nodes = {n.node_id: n for n in self.storage.list_nodes(workspace_id)}
        rels = self.storage.list_relationships(workspace_id)

        # Map each project/repo to the technologies it uses
        proj_techs = collections.defaultdict(set)
        for r in rels:
            if r.source_id in nodes and nodes[r.source_id].label in (EntityType.PROJECT, EntityType.REPOSITORY):
                if r.target_id in nodes and nodes[r.target_id].label in (
                    EntityType.TECHNOLOGY, EntityType.PROGRAMMING_LANGUAGE, EntityType.FRAMEWORK, EntityType.LIBRARY
                ):
                    proj_techs[r.source_id].add(nodes[r.target_id].name)

        # Count co-occurrence pairings
        pairing_counts = collections.Counter()
        for techs in proj_techs.values():
            tech_list = sorted(list(techs))
            for i in range(len(tech_list)):
                for j in range(i + 1, len(tech_list)):
                    pairing_counts[(tech_list[i], tech_list[j])] += 1

        # Group highly co-occurring technologies
        clusters = collections.defaultdict(list)
        for (t1, t2), count in pairing_counts.items():
            if count >= 1:  # Threshold can be increased for denser graphs
                clusters[t1].append(t2)
                clusters[t2].append(t1)

        return {k: sorted(list(set(v))) for k, v in clusters.items()}

    def _infer_tech_stacks(self, workspace_id: str) -> Dict[str, List[str]]:
        """Maps project nodes to their complete technology stack (languages, frameworks, libraries)."""
        nodes = {n.node_id: n for n in self.storage.list_nodes(workspace_id)}
        rels = self.storage.list_relationships(workspace_id)

        proj_nodes = [n for n in nodes.values() if n.label in (EntityType.PROJECT, EntityType.REPOSITORY)]
        stacks = {}

        for p in proj_nodes:
            tech_names = []
            for r in rels:
                if r.source_id == p.node_id and r.relationship_type == RelationshipType.USES:
                    target_node = nodes.get(r.target_id)
                    if target_node:
                        tech_names.append(target_node.name)
            if tech_names:
                stacks[p.name] = sorted(tech_names)

        return stacks
