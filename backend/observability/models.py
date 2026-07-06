"""Core Pydantic data schemas for the AI Observability & Telemetry Platform."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SpanStatus(str, Enum):
    """Execution outcome of a single trace span."""
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class ExportFormat(str, Enum):
    """Supported trace export formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"


# ---------------------------------------------------------------------------
# Trace primitives
# ---------------------------------------------------------------------------

class TraceSpan(BaseModel):
    """A single timed unit of work within an execution trace."""
    span_id: str = Field(default_factory=lambda: f"span-{uuid.uuid4().hex[:8]}")
    parent_span_id: Optional[str] = None
    name: str
    module: str = ""
    status: SpanStatus = SpanStatus.RUNNING
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""


class ReasoningStep(BaseModel):
    """A single step captured from the Reasoning Engine."""
    step_id: str = Field(default_factory=lambda: f"rs-{uuid.uuid4().hex[:8]}")
    span_id: str = ""
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MemoryAccess(BaseModel):
    """Records a read or write to the Memory subsystem."""
    access_id: str = Field(default_factory=lambda: f"mem-{uuid.uuid4().hex[:8]}")
    operation: str  # "read" | "write"
    key: str
    namespace: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class KnowledgeSourceRef(BaseModel):
    """Reference to a knowledge source consulted during execution."""
    source_id: str = Field(default_factory=lambda: f"ks-{uuid.uuid4().hex[:8]}")
    source_type: str  # "document", "ukp", "graph", etc.
    identifier: str
    relevance_score: float = 1.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PromptMetadata(BaseModel):
    """Metadata associated with a model prompt."""
    template_name: str = ""
    token_count: int = 0
    model: str = ""
    provider: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ResponseMetadata(BaseModel):
    """Metadata associated with a model response."""
    token_count: int = 0
    latency_ms: float = 0.0
    finish_reason: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Full execution trace
# ---------------------------------------------------------------------------

class ExecutionTrace(BaseModel):
    """Complete observability record for a single execution request."""
    trace_id: str = Field(default_factory=lambda: f"tr-{uuid.uuid4().hex[:8]}")
    execution_id: str
    workflow_id: str = ""
    workspace_id: str = ""
    agent_ids: List[str] = Field(default_factory=list)
    modules_executed: List[str] = Field(default_factory=list)
    spans: List[TraceSpan] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStep] = Field(default_factory=list)
    memory_accesses: List[MemoryAccess] = Field(default_factory=list)
    knowledge_sources: List[KnowledgeSourceRef] = Field(default_factory=list)
    prompt_metadata: Optional[PromptMetadata] = None
    response_metadata: Optional[ResponseMetadata] = None
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: str = ""
    total_duration_ms: float = 0.0
    status: SpanStatus = SpanStatus.RUNNING


# ---------------------------------------------------------------------------
# Model & performance metrics
# ---------------------------------------------------------------------------

class ModelMetrics(BaseModel):
    """Per-invocation metrics for a model call."""
    invocation_id: str = Field(default_factory=lambda: f"inv-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    workspace_id: str = ""
    provider: str
    model: str
    tokens_in: int = 0
    tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    latency_ms: float = 0.0
    retries: int = 0
    failed: bool = False
    streaming_duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PerformanceSnapshot(BaseModel):
    """Aggregated system performance metrics at a point in time."""
    avg_latency_ms: float = 0.0
    module_timings: Dict[str, float] = Field(default_factory=dict)
    slowest_operations: List[Dict[str, Any]] = Field(default_factory=list)
    cache_hit_rate: float = 0.0
    concurrent_requests: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Failure analysis
# ---------------------------------------------------------------------------

class FailureRecord(BaseModel):
    """Captures a failure event with diagnostic detail."""
    failure_id: str = Field(default_factory=lambda: f"fail-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    span_id: str = ""
    exception_type: str = ""
    message: str = ""
    stack_trace: str = ""
    retry_attempts: int = 0
    recovery_strategy: str = ""
    fallback_module: str = ""
    root_cause: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------

class TimelineEvent(BaseModel):
    """A single entry in an execution timeline."""
    event_id: str = Field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    execution_id: str = ""
    event_type: str
    description: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
