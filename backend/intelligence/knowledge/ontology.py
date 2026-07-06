"""Defines semantic schemas, validation constraints, and connection taxonomies for the Graph Ontology."""

from typing import Dict, Set
from backend.intelligence.knowledge.models import EntityType, RelationshipType


class GraphOntology:
    """Governs relationship constraints, valid connection pairs, and domain taxonomy checks."""

    # Defines allowed source -> edge -> target type mappings
    VALID_TRIPLES: Dict[RelationshipType, Set[tuple[EntityType, EntityType]]] = {
        RelationshipType.USES: {
            (EntityType.PERSON, EntityType.TECHNOLOGY),
            (EntityType.PERSON, EntityType.PROGRAMMING_LANGUAGE),
            (EntityType.PERSON, EntityType.FRAMEWORK),
            (EntityType.PERSON, EntityType.LIBRARY),
            (EntityType.PROJECT, EntityType.TECHNOLOGY),
            (EntityType.PROJECT, EntityType.PROGRAMMING_LANGUAGE),
            (EntityType.PROJECT, EntityType.FRAMEWORK),
            (EntityType.PROJECT, EntityType.LIBRARY),
            (EntityType.REPOSITORY, EntityType.LIBRARY),
            (EntityType.REPOSITORY, EntityType.FRAMEWORK),
        },
        RelationshipType.DEPENDS_ON: {
            (EntityType.PROJECT, EntityType.PROJECT),
            (EntityType.REPOSITORY, EntityType.REPOSITORY),
            (EntityType.FRAMEWORK, EntityType.PROGRAMMING_LANGUAGE),
            (EntityType.LIBRARY, EntityType.PROGRAMMING_LANGUAGE),
            (EntityType.TASK, EntityType.TASK),
        },
        RelationshipType.AUTHORED: {
            (EntityType.PERSON, EntityType.DOCUMENT),
            (EntityType.PERSON, EntityType.RESEARCH_PAPER),
            (EntityType.PERSON, EntityType.REPOSITORY),
            (EntityType.PERSON, EntityType.PROJECT),
        },
        RelationshipType.WORKED_ON: {
            (EntityType.PERSON, EntityType.PROJECT),
            (EntityType.PERSON, EntityType.REPOSITORY),
            (EntityType.PERSON, EntityType.TASK),
            (EntityType.PERSON, EntityType.COMPANY),
            (EntityType.PERSON, EntityType.ORGANIZATION),
        },
        RelationshipType.IMPLEMENTS: {
            (EntityType.PROJECT, EntityType.TOPIC),
            (EntityType.REPOSITORY, EntityType.TOPIC),
            (EntityType.FRAMEWORK, EntityType.TOPIC),
        },
        RelationshipType.EXTENDS: {
            (EntityType.FRAMEWORK, EntityType.FRAMEWORK),
            (EntityType.LIBRARY, EntityType.LIBRARY),
            (EntityType.PROGRAMMING_LANGUAGE, EntityType.PROGRAMMING_LANGUAGE),
        },
        RelationshipType.MENTIONS: {
            (EntityType.DOCUMENT, EntityType.PERSON),
            (EntityType.DOCUMENT, EntityType.TECHNOLOGY),
            (EntityType.DOCUMENT, EntityType.SKILL),
            (EntityType.MEETING, EntityType.PERSON),
            (EntityType.MEETING, EntityType.PROJECT),
            (EntityType.MEETING, EntityType.TASK),
        },
        RelationshipType.REFERENCES: {
            (EntityType.DOCUMENT, EntityType.DOCUMENT),
            (EntityType.RESEARCH_PAPER, EntityType.RESEARCH_PAPER),
            (EntityType.RESEARCH_PAPER, EntityType.DOCUMENT),
        },
        RelationshipType.PART_OF: {
            (EntityType.PROJECT, EntityType.REPOSITORY),
            (EntityType.REPOSITORY, EntityType.ORGANIZATION),
            (EntityType.SKILL, EntityType.TOPIC),
            (EntityType.TOPIC, EntityType.COURSE),
        },
        RelationshipType.LEARNS: {
            (EntityType.PERSON, EntityType.SKILL),
            (EntityType.PERSON, EntityType.COURSE),
            (EntityType.PERSON, EntityType.TOPIC),
        },
        RelationshipType.REQUIRES: {
            (EntityType.COURSE, EntityType.CERTIFICATION),
            (EntityType.TASK, EntityType.SKILL),
            (EntityType.CERTIFICATION, EntityType.SKILL),
        },
        RelationshipType.GENERATED_FROM: {
            (EntityType.DOCUMENT, EntityType.MEETING),
            (EntityType.TASK, EntityType.MEETING),
        }
    }

    def validate_relationship(
        self,
        source_label: EntityType,
        target_label: EntityType,
        relationship_type: RelationshipType
    ) -> bool:
        """Verifies if the connection complies with schema guidelines.

        Allows fallback/general connections (e.g. RELATED_TO or SIMILAR_TO) unconditionally.
        """
        # Generic fallback connections are globally allowed
        if relationship_type in (RelationshipType.RELATED_TO, RelationshipType.SIMILAR_TO):
            return True

        allowed_pairs = self.VALID_TRIPLES.get(relationship_type)
        if not allowed_pairs:
            return False

        return (source_label, target_label) in allowed_pairs
