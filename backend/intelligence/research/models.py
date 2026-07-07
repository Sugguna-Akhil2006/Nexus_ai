"""Data models for paper metadata and synthesised research analysis reports."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResearchPaperMetadata(BaseModel):
    """Metadata representing a parsed research paper or technical documentation."""
    paper_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    abstract: str
    published_date: Optional[str] = None
    venue: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class ResearchAnalysisReport(BaseModel):
    """Consolidated findings and matrix details synthesized from multiple sources."""
    report_id: str = Field(default_factory=lambda: "")
    executive_summary: str
    key_findings: List[str] = Field(default_factory=list)
    evidence_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    source_comparison: Dict[str, Any] = Field(default_factory=dict)
    topics: List[str] = Field(default_factory=list)
    knowledge_graph_updates: Dict[str, List[str]] = Field(default_factory=dict)
    research_gaps: List[str] = Field(default_factory=list)
    suggested_reading: List[str] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
