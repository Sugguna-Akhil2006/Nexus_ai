"""Standard response models returned by every intelligence module.

These are the stable outbound contracts consumed by the backend
platform (PJ), frontend (Tejus), and SDK.  They wrap the internal
``IntelligenceExecutionReport`` without exposing it directly.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class ResponseStatus(str, Enum):
    """Execution outcome classification."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# ---------------------------------------------------------------------------
# Supporting sub-models
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    """Reference to a knowledge source supporting the response."""

    citation_id: str = Field(default_factory=lambda: f"cit-{uuid.uuid4().hex[:8]}")
    source_type: str          # "document" | "url" | "knowledge_base" | "memory"
    identifier: str           # document ID, URL, or KB key
    title: str = ""
    snippet: str = ""
    relevance_score: float = 1.0
    page: Optional[int] = None


class Artifact(BaseModel):
    """A structured output artefact produced during execution."""

    artifact_id: str = Field(default_factory=lambda: f"art-{uuid.uuid4().hex[:8]}")
    artifact_type: str        # "report" | "chart_data" | "json_export" | "markdown"
    name: str
    content: Any              # string, dict, or list depending on artifact_type
    mime_type: str = "application/json"
    size_bytes: Optional[int] = None


class ExecutionMetrics(BaseModel):
    """Performance and cost metrics for the completed execution."""

    total_duration_ms: float = 0.0
    stage_timings: Dict[str, float] = Field(default_factory=dict)
    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    provider: str = ""
    model: str = ""
    retries: int = 0
    cache_hits: int = 0


class Recommendation(BaseModel):
    """An actionable suggestion surfaced by the intelligence analysis."""

    recommendation_id: str = Field(default_factory=lambda: f"rec-{uuid.uuid4().hex[:8]}")
    category: str
    title: str
    description: str
    priority: str = "medium"      # "low" | "medium" | "high" | "critical"
    evidence: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Standard Intelligence Response
# ---------------------------------------------------------------------------


class IntelligenceResponse(BaseModel):
    """Canonical response model returned by every intelligence module.

    Fields
    ------
    execution_id       : Mirrors ``IntelligenceExecutionReport.execution_id``.
    request_id         : Echo of the originating ``IntelligenceRequest.request_id``.
    module             : Module that produced this response.
    status             : Execution outcome (completed / partial / failed …).
    confidence         : Aggregate output confidence in [0.0, 1.0].
    summary            : Plain-text executive summary of the analysis.
    structured_output  : Module-specific typed payload (JSON-serialisable dict).
    artifacts          : Generated output artefacts (reports, charts, exports).
    citations          : Knowledge-source references supporting the output.
    execution_metrics  : Performance and cost metadata.
    recommendations    : Actionable suggestions from the analysis.
    errors             : Structured error descriptions (empty on success).
    completed_at       : ISO-8601 completion timestamp.
    """

    execution_id: str
    request_id: str
    module: str
    status: ResponseStatus
    confidence: float = 0.0
    summary: str = ""
    structured_output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[Artifact] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    execution_metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    recommendations: List[Recommendation] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    completed_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
