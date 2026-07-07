"""Core Enums defining valid entity node labels and relationship edge types."""

from enum import Enum


class EntityType(str, Enum):
    """Enums representing the classification types of Knowledge Graph nodes."""
    PERSON = "Person"
    SKILL = "Skill"
    TECHNOLOGY = "Technology"
    PROGRAMMING_LANGUAGE = "Programming Language"
    FRAMEWORK = "Framework"
    LIBRARY = "Library"
    COMPANY = "Company"
    ORGANIZATION = "Organization"
    PROJECT = "Project"
    REPOSITORY = "Repository"
    DOCUMENT = "Document"
    MEETING = "Meeting"
    TASK = "Task"
    RESEARCH_PAPER = "Research Paper"
    TOPIC = "Topic"
    COURSE = "Course"
    CERTIFICATION = "Certification"


class RelationshipType(str, Enum):
    """Enums representing the semantic relationship types of Knowledge Graph edges."""
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    AUTHORED = "AUTHORED"
    WORKED_ON = "WORKED_ON"
    RELATED_TO = "RELATED_TO"
    IMPLEMENTS = "IMPLEMENTS"
    EXTENDS = "EXTENDS"
    MENTIONS = "MENTIONS"
    REFERENCES = "REFERENCES"
    PART_OF = "PART_OF"
    SIMILAR_TO = "SIMILAR_TO"
    LEARNS = "LEARNS"
    REQUIRES = "REQUIRES"
    GENERATED_FROM = "GENERATED_FROM"
