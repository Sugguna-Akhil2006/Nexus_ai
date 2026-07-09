"""Streaming contract models for progressive intelligence responses.

Defines the wire format for SSE / WebSocket token streaming so that
the frontend (Tejus) and SDK can consume partial output incrementally.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Event kinds
# ---------------------------------------------------------------------------


class StreamEventKind(str, Enum):
    """Discriminator for each streaming event type."""

    PROGRESS = "progress"
    PARTIAL_RESPONSE = "partial_response"
    TOKEN = "token"
    COMPLETION = "completion"
    CANCELLATION = "cancellation"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Individual stream event models
# ---------------------------------------------------------------------------


class StreamProgressEvent(BaseModel):
    """Reports current stage and percentage completion."""

    kind: StreamEventKind = StreamEventKind.PROGRESS
    stream_id: str
    request_id: str
    stage: str
    message: str = ""
    percent_complete: float = 0.0          # 0–100
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamPartialResponseEvent(BaseModel):
    """Carries a partial structured output payload (e.g., early sections of a report)."""

    kind: StreamEventKind = StreamEventKind.PARTIAL_RESPONSE
    stream_id: str
    request_id: str
    partial_output: Dict[str, Any] = Field(default_factory=dict)
    is_final: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamTokenEvent(BaseModel):
    """Delivers a single token or token chunk for live text generation."""

    kind: StreamEventKind = StreamEventKind.TOKEN
    stream_id: str
    request_id: str
    token: str
    cumulative_tokens: int = 0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamCompletionEvent(BaseModel):
    """Signals the end of a streaming session with final metrics."""

    kind: StreamEventKind = StreamEventKind.COMPLETION
    stream_id: str
    request_id: str
    execution_id: str
    total_tokens: int = 0
    duration_ms: float = 0.0
    final_confidence: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamCancellationEvent(BaseModel):
    """Published when the caller or system cancels a streaming request."""

    kind: StreamEventKind = StreamEventKind.CANCELLATION
    stream_id: str
    request_id: str
    reason: str = "caller_cancelled"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StreamErrorEvent(BaseModel):
    """Published when an error terminates the stream prematurely."""

    kind: StreamEventKind = StreamEventKind.ERROR
    stream_id: str
    request_id: str
    error_code: str
    message: str
    recoverable: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Stream session descriptor
# ---------------------------------------------------------------------------


class StreamSession(BaseModel):
    """Descriptor created when a streaming request is opened."""

    stream_id: str = Field(default_factory=lambda: f"stream-{uuid.uuid4().hex[:10]}")
    request_id: str
    module: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    cancelled: bool = False
    completed: bool = False
