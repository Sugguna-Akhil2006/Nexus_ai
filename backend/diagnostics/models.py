"""Pydantic data models for the Production Diagnostics & Observability Console."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Standardized classification of execution errors."""

    VALIDATION = "validation"
    PROVIDER = "provider"
    TIMEOUT = "timeout"
    WORKFLOW = "workflow"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"


class TimelineStep(BaseModel):
    """A milestone event in the lifetime of a request."""

    step_name: str
    step_type: str  # "module" | "gateway" | "orchestrator" | "stream"
    status: str  # "pending" | "running" | "completed" | "failed"
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ProviderMetricSummary(BaseModel):
    """Execution telemetry recorded for a single AI provider."""

    provider_name: str
    total_calls: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    failures: int = 0
    fallbacks: int = 0
    avg_latency_ms: float = 0.0
    fallback_rate: float = 0.0


class ErrorRecord(BaseModel):
    """Chronological error record for analysis."""

    error_id: str
    request_id: str
    category: ErrorCategory
    message: str
    module_name: Optional[str] = None
    timestamp: str


class RequestTrace(BaseModel):
    """Complete diagnostic representation of a processed query request."""

    request_id: str
    workspace_id: str
    user_id: str
    status: str
    duration_ms: float = 0.0
    modules_used: List[str] = Field(default_factory=list)
    providers_used: List[str] = Field(default_factory=list)
    retries: int = 0
    errors: Dict[str, str] = Field(default_factory=dict)
    timeline: List[TimelineStep] = Field(default_factory=list)
    created_at: str
