"""Ingests intelligence feeds from Resume, GitHub, and Document systems into the Knowledge Graph."""

import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from backend.intelligence.knowledge.entity_node import EntityNode
from backend.intelligence.knowledge.relationship import Relationship
from backend.intelligence.knowledge.models import EntityType, RelationshipType
from backend.intelligence.knowledge.graph_storage import GraphStorage
from backend.intelligence.knowledge.graph_merger import GraphMerger


class GraphBuilder:
    """Constructs and merges semantic entities and relationships from profile data feeds."""

    def __init__(self, storage: GraphStorage) -> None:
        self.storage = storage
        self.merger = GraphMerger()

    def add_or_merge_node(self, workspace_id: str, node: EntityNode) -> str:
        """Adds a node to storage. If a duplicate exists, merges them and returns the original node_id."""
        existing_nodes = self.storage.list_nodes(workspace_id)
        
        for ext in existing_nodes:
            if self.merger.should_merge_nodes(ext, node):
                merged = self.merger.merge_nodes(ext, node)
                self.storage.upsert_node(workspace_id, merged)
                return ext.node_id
        
        self.storage.upsert_node(workspace_id, node)
        return node.node_id

    def add_or_merge_relationship(self, workspace_id: str, rel: Relationship) -> None:
        """Adds a relationship, merging with duplicates if same source, target, and type exist."""
        existing_rels = self.storage.list_relationships(workspace_id)
        
        for ext in existing_rels:
            if ext.source_id == rel.source_id and ext.target_id == rel.target_id and ext.relationship_type == rel.relationship_type:
                merged = self.merger.merge_relationships(ext, rel)
                self.storage.upsert_relationship(workspace_id, merged)
                return

        self.storage.upsert_relationship(workspace_id, rel)

    def build_from_resume(self, workspace_id: str, profile_data: Dict[str, Any]) -> None:
        """Translates Resume profile elements (skills, projects, experiences) to graph elements."""
        person_name = profile_data.get("personal_info", {}).get("full_name") or "Professional"
        user_id = profile_data.get("user_id") or f"user-{str(uuid.uuid4())[:8]}"

        # 1. Create Person node
        person_node = EntityNode(
            node_id=f"person-{user_id}",
            label=EntityType.PERSON,
            name=person_name,
            properties={
                "email": profile_data.get("personal_info", {}).get("email") or "",
                "github": profile_data.get("personal_info", {}).get("github") or ""
            },
            confidence=1.0,
            evidence_sources=["Resume"]
        )
        person_id = self.add_or_merge_node(workspace_id, person_node)

        # 2. Ingest skills
        skills = profile_data.get("skills", {})
        for skill_name, skill_val in skills.items():
            skill_node = EntityNode(
                node_id=f"skill-{self.merger.normalize_name(skill_name)}",
                label=EntityType.SKILL,
                name=skill_name,
                properties={"category": skill_val.get("category") or "General"},
                confidence=skill_val.get("confidence_score") or 1.0,
                evidence_sources=["Resume"]
            )
            skill_id = self.add_or_merge_node(workspace_id, skill_node)

            # Link Person -> LEARNS/USES -> Skill
            self.add_or_merge_relationship(workspace_id, Relationship(
                relationship_id=f"rel-{person_id}-{skill_id}",
                source_id=person_id,
                target_id=skill_id,
                relationship_type=RelationshipType.LEARNS,
                confidence=1.0,
                evidence_sources=["Resume"]
            ))

        # 3. Ingest projects
        projects = profile_data.get("projects", [])
        for proj in projects:
            proj_name = proj.get("name") or "Unnamed Project"
            proj_node = EntityNode(
                node_id=f"proj-{self.merger.normalize_name(proj_name)}",
                label=EntityType.PROJECT,
                name=proj_name,
                properties={"description": proj.get("description") or ""},
                confidence=1.0,
                evidence_sources=["Resume"]
            )
            proj_id = self.add_or_merge_node(workspace_id, proj_node)

            # Link Person -> WORKED_ON -> Project
            self.add_or_merge_relationship(workspace_id, Relationship(
                relationship_id=f"rel-{person_id}-{proj_id}",
                source_id=person_id,
                target_id=proj_id,
                relationship_type=RelationshipType.WORKED_ON,
                confidence=1.0,
                evidence_sources=["Resume"]
            ))

            # Link Project -> USES -> Technologies
            for tech in proj.get("technologies", []):
                tech_node = EntityNode(
                    node_id=f"tech-{self.merger.normalize_name(tech)}",
                    label=EntityType.TECHNOLOGY,
                    name=tech,
                    confidence=1.0,
                    evidence_sources=["Resume"]
                )
                tech_id = self.add_or_merge_node(workspace_id, tech_node)

                self.add_or_merge_relationship(workspace_id, Relationship(
                    relationship_id=f"rel-{proj_id}-{tech_id}",
                    source_id=proj_id,
                    target_id=tech_id,
                    relationship_type=RelationshipType.USES,
                    confidence=1.0,
                    evidence_sources=["Resume"]
                ))

        # 4. Ingest experience
        experience = profile_data.get("experience", [])
        for exp in experience:
            company = exp.get("company") or "Unnamed Company"
            company_node = EntityNode(
                node_id=f"company-{self.merger.normalize_name(company)}",
                label=EntityType.COMPANY,
                name=company,
                properties={"role": exp.get("role") or ""},
                confidence=1.0,
                evidence_sources=["Resume"]
            )
            company_id = self.add_or_merge_node(workspace_id, company_node)

            # Link Person -> WORKED_ON -> Company
            self.add_or_merge_relationship(workspace_id, Relationship(
                relationship_id=f"rel-{person_id}-{company_id}",
                source_id=person_id,
                target_id=company_id,
                relationship_type=RelationshipType.WORKED_ON,
                confidence=1.0,
                evidence_sources=["Resume"]
            ))

    def build_from_github(self, workspace_id: str, github_report: Dict[str, Any]) -> None:
        """Translates GitHub repositories, programming languages, and authors into the graph."""
        repos = github_report.get("repositories", [])
        
        # Link Repo to USES language
        for repo in repos:
            repo_name = repo.get("name") or "Unnamed Repo"
            repo_node = EntityNode(
                node_id=f"repo-{self.merger.normalize_name(repo_name)}",
                label=EntityType.REPOSITORY,
                name=repo_name,
                properties={"stars": repo.get("stars", 0), "forks": repo.get("forks", 0)},
                confidence=1.0,
                evidence_sources=["GitHub"]
            )
            repo_id = self.add_or_merge_node(workspace_id, repo_node)

            # Link main programming language
            lang = repo.get("language") or repo.get("programming_language")
            if lang:
                lang_node = EntityNode(
                    node_id=f"lang-{self.merger.normalize_name(lang)}",
                    label=EntityType.PROGRAMMING_LANGUAGE,
                    name=lang,
                    confidence=1.0,
                    evidence_sources=["GitHub"]
                )
                lang_id = self.add_or_merge_node(workspace_id, lang_node)

                self.add_or_merge_relationship(workspace_id, Relationship(
                    relationship_id=f"rel-{repo_id}-{lang_id}",
                    source_id=repo_id,
                    target_id=lang_id,
                    relationship_type=RelationshipType.USES,
                    confidence=1.0,
                    evidence_sources=["GitHub"]
                ))

            # Link author
            author_name = repo.get("author") or repo.get("owner")
            if author_name:
                author_node = EntityNode(
                    node_id=f"person-{self.merger.normalize_name(author_name)}",
                    label=EntityType.PERSON,
                    name=author_name,
                    confidence=1.0,
                    evidence_sources=["GitHub"]
                )
                author_id = self.add_or_merge_node(workspace_id, author_node)

                # Link Person -> AUTHORED -> Repository
                self.add_or_merge_relationship(workspace_id, Relationship(
                    relationship_id=f"rel-{author_id}-{repo_id}",
                    source_id=author_id,
                    target_id=repo_id,
                    relationship_type=RelationshipType.AUTHORED,
                    confidence=1.0,
                    evidence_sources=["GitHub"]
                ))

    def build_from_document(self, workspace_id: str, document_report: Dict[str, Any]) -> None:
        """Translates Document metadata and extracted entities into the graph."""
        doc_name = document_report.get("name") or "Unnamed Document"
        doc_id_raw = document_report.get("document_id") or f"doc-{str(uuid.uuid4())[:8]}"

        # 1. Create Document node
        doc_node = EntityNode(
            node_id=f"doc-{doc_id_raw}",
            label=EntityType.DOCUMENT,
            name=doc_name,
            properties={"author": document_report.get("author") or ""},
            confidence=1.0,
            evidence_sources=["Document"]
        )
        doc_id = self.add_or_merge_node(workspace_id, doc_node)

        # 2. Add mentioned skills
        skills = document_report.get("skills") or document_report.get("extracted_skills") or []
        for skill in skills:
            skill_node = EntityNode(
                node_id=f"skill-{self.merger.normalize_name(skill)}",
                label=EntityType.SKILL,
                name=skill,
                confidence=0.8,  # Lower starting confidence since extracted via parsing
                evidence_sources=["Document"],
                supporting_documents=[doc_id_raw]
            )
            skill_id = self.add_or_merge_node(workspace_id, skill_node)

            # Link Document -> MENTIONS -> Skill
            self.add_or_merge_relationship(workspace_id, Relationship(
                relationship_id=f"rel-{doc_id}-{skill_id}",
                source_id=doc_id,
                target_id=skill_id,
                relationship_type=RelationshipType.MENTIONS,
                confidence=0.8,
                evidence_sources=["Document"],
                supporting_documents=[doc_id_raw]
            ))
