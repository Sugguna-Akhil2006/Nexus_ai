"""Data schemas for Evidence, Conflict, ReasoningRequest, and ReasoningReport."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Represents a single fact extracted from an intelligence source."""
    evidence_id: str
    source: str  # "Resume", "GitHub", "Document", "Knowledge Profile", etc.
    fact: str
    confidence: float = 1.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Conflict(BaseModel):
    """Represents a contradiction or redundancy detected in the evidence pool."""
    conflict_id: str
    category: str  # "Contradiction", "Duplicate", "Low Confidence", "Missing Evidence"
    description: str
    offending_sources: List[str] = Field(default_factory=list)
    severity: str = "Medium"  # "Low", "Medium", "High"


class ReasoningRequest(BaseModel):
    """Parameters representing the query and input evidence pool to reason over."""
    workspace_id: str
    query: str
    sources: List[Evidence] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)


class ReasoningReport(BaseModel):
    """The structured result representing the final conclusions and reasoning traces."""
    report_id: str
    query: str
    collected_evidence: List[Evidence] = Field(default_factory=list)
    supporting_sources: List[str] = Field(default_factory=list)
    confidence: float
    detected_conflicts: List[Conflict] = Field(default_factory=list)
    final_conclusions: List[str] = Field(default_factory=list)
    reasoning_trace: List[str] = Field(default_factory=list)
