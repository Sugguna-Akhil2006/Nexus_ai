"""Standard request models for every intelligence module.

These models form the stable inbound contract consumed by the backend
platform, frontend, and SDK.  Intelligence module internals are NOT
imported here — contracts are decoupled from implementations.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Module identifiers
# ---------------------------------------------------------------------------


class IntelligenceModule(str, Enum):
    """Registered intelligence modules available for invocation."""

    RESUME = "resume"
    GITHUB = "github"
    DOCUMENT = "document"
    CAREER = "career"
    PROFESSIONAL = "professional"
    KNOWLEDGE = "knowledge"
    RESEARCH = "research"
    LEARNING = "learning"
    COLLABORATION = "collaboration"
    REASONING = "reasoning"


# ---------------------------------------------------------------------------
# Attachment
# ---------------------------------------------------------------------------


class AttachmentType(str, Enum):
    """Supported binary / reference attachment types."""

    PDF = "pdf"
    DOCX = "docx"
    MARKDOWN = "markdown"
    TEXT = "text"
    URL = "url"
    JSON = "json"
    IMAGE = "image"


class Attachment(BaseModel):
    """A file or URL reference passed alongside the intelligence request."""

    attachment_id: str = Field(default_factory=lambda: f"att-{uuid.uuid4().hex[:8]}")
    name: str
    attachment_type: AttachmentType
    content_base64: Optional[str] = None   # base-64 encoded binary payload
    url: Optional[str] = None              # remote URL reference
    size_bytes: Optional[int] = None
    mime_type: str = "application/octet-stream"
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Options & metadata
# ---------------------------------------------------------------------------


class RequestOptions(BaseModel):
    """Execution-level knobs that callers may tune per-request."""

    stream: bool = False                        # enable streaming response
    max_tokens: Optional[int] = None            # cap on output tokens
    temperature: float = 0.7
    timeout_seconds: int = 120
    language: str = "en"
    output_format: str = "json"                 # "json" | "markdown" | "text"
    include_citations: bool = True
    include_reasoning_trace: bool = False
    custom: Dict[str, Any] = Field(default_factory=dict)


class RequestMetadata(BaseModel):
    """Caller-supplied tracing metadata attached to every request."""

    source: str = ""               # e.g., "frontend", "sdk", "backend"
    version: str = "1.0"
    correlation_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    extra: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Standard Intelligence Request
# ---------------------------------------------------------------------------


class IntelligenceRequest(BaseModel):
    """Canonical request model consumed by every intelligence module.

    Fields
    ------
    request_id    : Auto-generated unique request identifier.
    workspace_id  : Tenant / workspace scope for the request.
    user_id       : Originating user identifier.
    session_id    : Optional session for stateful intelligence.
    module        : Target intelligence module.
    input         : Free-form input payload (query, document text, URLs …).
    attachments   : Binary or URL attachments for the module to process.
    options       : Per-request execution options.
    metadata      : Caller tracing metadata.
    created_at    : ISO-8601 creation timestamp.
    """

    request_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:12]}")
    workspace_id: str
    user_id: str
    session_id: Optional[str] = None
    module: IntelligenceModule
    input: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Attachment] = Field(default_factory=list)
    options: RequestOptions = Field(default_factory=RequestOptions)
    metadata: RequestMetadata = Field(default_factory=RequestMetadata)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )

    @field_validator("workspace_id", "user_id")
    @classmethod
    def _non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("workspace_id and user_id must be non-empty strings.")
        return v.strip()
