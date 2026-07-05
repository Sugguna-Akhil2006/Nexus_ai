"""Pydantic data models for Intelligent Document Ingestion, Graphs, and Indices."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from backend.intelligence.document.document_model import (
    DocumentMetadata,
    SummaryDetail,
    Topic,
    Entity,
    Citation,
    SimilarityMapping
)


class EntityNode(BaseModel):
    """A node in the Knowledge Graph representing an extracted entity."""
    name: str
    category: str  # Person, Organization, Location, Date, Technology, Standards, Project, etc.
    confidence: float


class RelationshipEdge(BaseModel):
    """A directed edge in the Knowledge Graph connecting two entities."""
    source: str  # Source entity name
    target: str  # Target entity name
    relationship_type: str  # e.g., "written_in", "deploys_to", "manages", "implements"
    confidence: float


class DocumentGraph(BaseModel):
    """Directed Knowledge Graph structure."""
    nodes: List[EntityNode] = Field(default_factory=list)
    edges: List[RelationshipEdge] = Field(default_factory=list)


class KnowledgeObject(BaseModel):
    """Generated structured evidence knowledge fact."""
    title: str
    description: str
    confidence: float
    evidence: str
    category: str = "Project"
    source_sections: List[str] = Field(default_factory=list)
    supporting_citations: List[str] = Field(default_factory=list)


class SemanticIndex(BaseModel):
    """Reusable semantic index structure for targeted concept/entity queries."""
    concept_index: Dict[str, List[str]] = Field(default_factory=dict)  # query -> list of chunk text/ids
    entity_index: Dict[str, List[str]] = Field(default_factory=dict)   # entity -> list of chunk text/ids
    topic_index: Dict[str, List[str]] = Field(default_factory=dict)    # topic -> list of chunk text/ids
    citation_index: Dict[str, List[str]] = Field(default_factory=dict) # citation key -> list of chunk text/ids


class ConfidenceScores(BaseModel):
    """Confidence metrics summary for the IDP pipeline execution."""
    metadata_confidence: float
    entity_confidence: float
    topic_confidence: float
    relationship_confidence: float
    overall_score: float


class DocumentKnowledgeReport(BaseModel):
    """Consolidated Knowledge Report constructed from the IDP Reasoning Engine."""
    report_id: str
    workspace_id: str
    document_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, DocumentMetadata] = Field(default_factory=dict)
    entities: List[EntityNode] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list)
    relationships: List[RelationshipEdge] = Field(default_factory=list)
    knowledge_graph: DocumentGraph
    semantic_index: SemanticIndex
    summary: SummaryDetail
    citations: List[Citation] = Field(default_factory=list)
    confidence_scores: ConfidenceScores
    knowledge_objects: List[KnowledgeObject] = Field(default_factory=list)
    extracted_knowledge: List[KnowledgeObject] = Field(default_factory=list)
    similar_documents: List[SimilarityMapping] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# API Payloads

class ProcessRequest(BaseModel):
    """Request payload to trigger IDP analysis."""
    workspace_id: str = "default-ws"
    document_ids: List[str]
    user_id: str = "admin"
    options: Optional[Dict[str, Any]] = None


class SearchIndexRequest(BaseModel):
    """Request payload to query a semantic index."""
    report_id: str
    search_type: str  # concept, entity, topic, citation
    query: str
