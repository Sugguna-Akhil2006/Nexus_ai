"""Pydantic data models for Document Intelligence models and reports."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata attributes extracted from a document."""
    title: str
    author: Optional[str] = None
    creation_date: Optional[str] = None
    format: str  # PDF, DOCX, TXT, MD, etc.
    word_count: int = 0
    line_count: int = 0
    keywords: List[str] = Field(default_factory=list)
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class SummaryDetail(BaseModel):
    """Different summarization styles for a document or collection."""
    executive: str = ""
    technical: str = ""
    bullet: List[str] = Field(default_factory=list)
    section_by_section: Dict[str, str] = Field(default_factory=dict)
    custom: Optional[str] = None


class Topic(BaseModel):
    """A main topic or theme discussed in the document."""
    name: str
    weight: float  # Confidence/importance score between 0.0 and 1.0
    description: str


class Entity(BaseModel):
    """A named entity extracted from the document text."""
    name: str
    label: str  # Person, Organization, Location, Date, Technology, etc.
    confidence: float


class Citation(BaseModel):
    """Reference citation linking answers to source document segments."""
    document_id: str
    document_name: str
    section: str  # Section header, page number, or block ID
    text_chunk: str
    chunk_id: Optional[str] = None
    confidence: Optional[float] = None
    evidence: Optional[str] = None


class SimilarityMapping(BaseModel):
    """Relationship mapping representing document-to-document similarity."""
    target_document_id: str
    target_document_name: str
    similarity_score: float  # Score from 0.0 to 1.0
    common_topics: List[str] = Field(default_factory=list)


class ExtractedKnowledgeItem(BaseModel):
    """Reusable professional knowledge facts contributing to Knowledge Profile."""
    key: str
    value: Any
    category: str  # Skill, Project, Experience, Certificate, etc.
    sources: List[str] = Field(default_factory=list)  # Document IDs


class DocumentAnalysisReport(BaseModel):
    """Unified Document Analysis Report containing extracted insights."""
    report_id: str
    workspace_id: str
    document_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, DocumentMetadata] = Field(default_factory=dict)  # Key is document_id
    summary: SummaryDetail
    topics: List[Topic] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    similar_documents: List[SimilarityMapping] = Field(default_factory=list)
    extracted_knowledge: List[ExtractedKnowledgeItem] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# API Payloads

class UploadResponse(BaseModel):
    """Response returned upon successful file ingestion/upload."""
    document_id: str
    filename: str
    mime_type: str
    file_size: int
    checksum: str
    uploaded_at: datetime


class AnalyzeRequest(BaseModel):
    """Request payload to initiate analysis on ingested documents."""
    workspace_id: str = "default-ws"
    document_ids: List[str]
    options: Optional[Dict[str, Any]] = None


class QueryRequest(BaseModel):
    """Request payload to query the document collection."""
    workspace_id: str = "default-ws"
    document_ids: List[str]
    query: str
    options: Optional[Dict[str, Any]] = None


class QueryResponse(BaseModel):
    """Query result response containing citation references."""
    query: str
    answer: str
    citations: List[Citation] = Field(default_factory=list)
