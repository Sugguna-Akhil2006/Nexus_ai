"""Standardized Execution Report model returned by all intelligence workflows."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class IntelligenceExecutionReport(BaseModel):
    """Execution metrics, timing timeline, warnings, and result payloads."""
    execution_id: str
    module_name: str
    status: str  # completed, failed, cancelled, partial_success
    execution_timeline: Dict[str, float] = Field(default_factory=dict)
    stage_results: Dict[str, Any] = Field(default_factory=dict)
    errors: Dict[str, str] = Field(default_factory=dict)
    warnings: Dict[str, List[str]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    output_summary: Dict[str, Any] = Field(default_factory=dict)
