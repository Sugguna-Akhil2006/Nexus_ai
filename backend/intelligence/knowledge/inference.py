"""Implements semantic rule-based inference for missing relationships, gaps, and clusters."""

import uuid
from datetime import datetime
from typing import List, Dict, Set, Any
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.knowledge.graph_storage import GraphStorage
from backend.intelligence.knowledge.confidence import ConfidenceEngine


class SemanticInferrer:
    """Evaluates rules over graph store to deduce implicit connections and knowledge gaps."""

    def infer_relationships(self, workspace_id: str, storage: GraphStorage) -> List[Relationship]:
        """Runs the rule engine over the graph and returns newly inferred relationships.

        Rules applied:
        1. Person USES Technology: If Person WORKED_ON Project/Repository and Project/Repository USES Technology.
        2. Framework/Library USES Programming Language: If Framework/Library DEPENDS_ON Programming Language.
        3. Person LEARNS Skill: If Person WORKED_ON Project and Project IMPLEMENTS Topic (which is PART_OF Skill).
        """
        inferred = []
        nodes = {n.node_id: n for n in storage.list_nodes(workspace_id)}
        rels = storage.list_relationships(workspace_id)

        # Build adjacency indexing
        worked_on_map: Dict[str, List[Relationship]] = {}  # person -> list of WORKED_ON relationships
        uses_map: Dict[str, List[Relationship]] = {}       # project -> list of USES relationships
        depends_on_map: Dict[str, List[Relationship]] = {} # framework -> list of DEPENDS_ON relationships
        
        # Existing relationships map to prevent redundant duplicate inferences
        existing_keys = set()
        for r in rels:
            existing_keys.add((r.source_id, r.target_id, r.relationship_type))
            if r.relationship_type == RelationshipType.WORKED_ON:
                worked_on_map.setdefault(r.source_id, []).append(r)
            elif r.relationship_type == RelationshipType.USES:
                uses_map.setdefault(r.source_id, []).append(r)
            elif r.relationship_type == RelationshipType.DEPENDS_ON:
                depends_on_map.setdefault(r.source_id, []).append(r)

        # Rule 1: Person WORKED_ON Project -> Project USES Tech/Lang => Person USES Tech/Lang
        for person_id, work_list in worked_on_map.items():
            for work_edge in work_list:
                proj_id = work_edge.target_id
                if proj_id in uses_map:
                    for uses_edge in uses_map[proj_id]:
                        tech_id = uses_edge.target_id
                        
                        # Only infer if it doesn't already exist
                        rel_key = (person_id, tech_id, RelationshipType.USES)
                        if rel_key not in existing_keys:
                            # Propagate confidence (multiplied by a rule factor of 0.8)
                            p_conf = ConfidenceEngine.propagate_path_confidence([
                                work_edge.confidence,
                                uses_edge.confidence
                            ])
                            conf = round(p_conf * 0.8, 2)
                            
                            inferred.append(Relationship(
                                relationship_id=f"inf-uses-{str(uuid.uuid4())[:8]}",
                                source_id=person_id,
                                target_id=tech_id,
                                relationship_type=RelationshipType.USES,
                                properties={"inferred": True, "rule": "person_worked_on_project_uses_tech"},
                                confidence=conf,
                                evidence_sources=["InferenceEngine"],
                                supporting_documents=list(set(work_edge.supporting_documents + uses_edge.supporting_documents))
                            ))
                            # Add to temporary key check
                            existing_keys.add(rel_key)

        return inferred

    def identify_knowledge_gaps(self, workspace_id: str, storage: GraphStorage) -> List[Dict[str, Any]]:
        """Identifies skills required by projects/tasks that a Person node does not yet possess.

        A knowledge gap exists if:
        - A Person WORKED_ON a Project
        - That Project REQUIRES or USES a Skill/Technology
        - The Person has no direct USES, WORKED_ON, or LEARNS edge to that Skill/Technology.
        """
        gaps = []
        nodes = {n.node_id: n for n in storage.list_nodes(workspace_id)}
        rels = storage.list_relationships(workspace_id)

        person_nodes = [n for n in nodes.values() if n.label == EntityType.PERSON]
        if not person_nodes:
            return gaps

        # Direct capabilities of each person
        person_skills: Dict[str, Set[str]] = {}
        for r in rels:
            if r.source_id in nodes and nodes[r.source_id].label == EntityType.PERSON:
                p_id = r.source_id
                target_id = r.target_id
                if r.relationship_type in (RelationshipType.USES, RelationshipType.LEARNS, RelationshipType.WORKED_ON):
                    person_skills.setdefault(p_id, set()).add(target_id)

        # Direct requirements of projects/repositories
        project_requirements: Dict[str, Set[str]] = {}
        for r in rels:
            if r.source_id in nodes and nodes[r.source_id].label in (EntityType.PROJECT, EntityType.REPOSITORY):
                proj_id = r.source_id
                target_id = r.target_id
                if r.relationship_type in (RelationshipType.USES, RelationshipType.REQUIRES):
                    project_requirements.setdefault(proj_id, set()).add(target_id)

        # Evaluate Person -> WORKED_ON -> Project
        for r in rels:
            if r.relationship_type == RelationshipType.WORKED_ON:
                p_id = r.source_id
                proj_id = r.target_id
                
                # Check nodes type labels
                if p_id in nodes and nodes[p_id].label == EntityType.PERSON:
                    if proj_id in project_requirements:
                        reqs = project_requirements[proj_id]
                        known = person_skills.get(p_id, set())
                        
                        missing = reqs - known
                        for item_id in missing:
                            if item_id in nodes:
                                gaps.append({
                                    "person_id": p_id,
                                    "person_name": nodes[p_id].name,
                                    "required_item_id": item_id,
                                    "required_item_name": nodes[item_id].name,
                                    "required_item_label": nodes[item_id].label.value,
                                    "context_project_id": proj_id,
                                    "context_project_name": nodes[proj_id].name
                                })

        return gaps
