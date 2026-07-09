"""Frontend integration data contracts.

These are the wire-format models shared between the backend integration
layer and the frontend.  They are deliberately simpler than the full
IntelligenceResponse contract so the frontend can consume them directly
without any transformation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class WorkflowEventKind(str, Enum):
    """Discriminator for every frontend-bound event."""

    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PROGRESS = "workflow.progress"
    MODULE_STARTED = "module.started"
    MODULE_COMPLETED = "module.completed"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    STREAM_TOKEN = "stream.token"
    STREAM_DONE = "stream.done"
    ERROR = "error"


class ReportFormat(str, Enum):
    """Output format requested by the frontend."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF_METADATA = "pdf_metadata"


# ---------------------------------------------------------------------------
# Frontend event envelope
# ---------------------------------------------------------------------------


class FrontendEvent(BaseModel):
    """Universal envelope for every server→frontend event."""

    event_id: str = Field(default_factory=lambda: f"fe-{uuid.uuid4().hex[:8]}")
    kind: WorkflowEventKind
    request_id: str
    workspace_id: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Progress events
# ---------------------------------------------------------------------------


class WorkflowStartedEvent(BaseModel):
    """Published when a multi-module workflow begins."""

    request_id: str
    workspace_id: str
    modules: List[str]
    total_modules: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class WorkflowProgressEvent(BaseModel):
    """Published after each module completes, carrying aggregate progress."""

    request_id: str
    completed_modules: int
    total_modules: int
    percent_complete: float           # 0–100
    current_module: str
    elapsed_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ModuleStartedEvent(BaseModel):
    """Published when a single module begins execution."""

    request_id: str
    module: str
    sequence_index: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ModuleCompletedEvent(BaseModel):
    """Published when a single module finishes successfully."""

    request_id: str
    module: str
    confidence: float
    duration_ms: float
    finding_count: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Final report / error events
# ---------------------------------------------------------------------------


class AnalysisCompletedEvent(BaseModel):
    """Carries the final composed report to the frontend."""

    request_id: str
    composition_id: str
    executive_summary: str
    overall_confidence: float
    participating_modules: List[str]
    total_duration_ms: float
    total_cost_usd: float
    finding_count: int
    recommendation_count: int
    citation_count: int
    conflict_count: int
    artifact_manifest: List[Dict[str, str]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisFailedEvent(BaseModel):
    """Published when the composition or a critical module fails."""

    request_id: str
    error_code: str
    message: str
    failed_module: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Streaming token events
# ---------------------------------------------------------------------------


class StreamTokenEvent(BaseModel):
    """A single token chunk pushed to the frontend during text generation."""

    request_id: str
    module: str
    token: str
    cumulative_tokens: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamDoneEvent(BaseModel):
    """Published when a streaming generation is complete."""

    request_id: str
    module: str
    total_tokens: int
    duration_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Report format response
# ---------------------------------------------------------------------------


class FormattedReport(BaseModel):
    """A report rendered in the format requested by the frontend."""

    request_id: str
    format: ReportFormat
    content: str                        # serialized report body
    content_type: str                   # MIME type
    size_bytes: int = 0
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Artifact download descriptor
# ---------------------------------------------------------------------------


class ArtifactDownload(BaseModel):
    """Descriptor for a downloadable artifact."""

    artifact_id: str
    name: str
    artifact_type: str
    mime_type: str
    download_url: str                   # pre-signed or relative URL
    size_bytes: Optional[int] = None
    expires_at: Optional[str] = None
