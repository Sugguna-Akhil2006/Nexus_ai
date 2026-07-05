"""Defines document processing workflow stages, orchestrator loops, and exceptions."""

from enum import Enum


class DocumentStageNames(str, Enum):
    LOADER = "Document Ingestion & Parsing"
    CHUNKING = "Semantic Text Chunking"
    ANALYSIS = "Metadata & Entity Extraction"
    SIMILARITY = "Cross-Document Similarity"
    SUMMARIZATION = "Multi-style Summarization"
    KNOWLEDGE_PROFILE = "Knowledge Profile Update"
    REPORT = "Document Report Construction"


class DocumentIntelligenceError(Exception):
    """Base exception for all Document Intelligence module errors."""
    pass


class StageExecutionError(DocumentIntelligenceError):
    """Raised when a specific step in the Document Ingestion pipeline fails."""
    def __init__(self, stage_name: DocumentStageNames, message: str) -> None:
        self.stage_name = stage_name
        self.message = message
        super().__init__(f"Stage '{stage_name.value}' failed: {message}")
