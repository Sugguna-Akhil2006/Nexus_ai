"""Pydantic data models for the Cross-Intelligence Orchestrator execution plans and responses."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OrchestrationRequest(BaseModel):
    """Structured request representing the query, files, and settings for orchestration."""
    workspace_id: str
    user_id: str
    query: str
    document_ids: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)


class ExecutionStep(BaseModel):
    """A single step mapping to an intelligence module run execution."""
    step_id: str
    module_name: str  # "Resume", "GitHub", "Document", "Research"
    action: str  # "analyze", "compare", "evaluate"
    dependencies: List[str] = Field(default_factory=list)  # step_ids that must complete first


class OrchestrationPlan(BaseModel):
    """The parallel or sequential plan to resolve the user query."""
    plan_id: str
    steps: List[ExecutionStep] = Field(default_factory=list)
    execution_mode: str = "PARALLEL"  # "PARALLEL" or "SEQUENTIAL"


class UnifiedIntelligenceResponse(BaseModel):
    """Structured response aggregating results from all executed intelligence modules."""
    response_id: str
    modules_executed: List[str] = Field(default_factory=list)
    execution_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_sources: List[str] = Field(default_factory=list)
    confidence_score: float
    reasoning_summary: str
    final_response: str
