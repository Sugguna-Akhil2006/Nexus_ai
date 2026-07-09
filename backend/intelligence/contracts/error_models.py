"""Standardized error contract for the Intelligence API.

Provides a consistent wire format for every error class so that the
backend, frontend, and SDK can handle failures uniformly without
inspecting internal exception hierarchies.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------


class ErrorCode(str, Enum):
    """Standardized machine-readable error codes."""

    # Request / input errors
    VALIDATION_ERROR = "validation_error"
    MISSING_FIELD = "missing_field"
    INVALID_MODULE = "invalid_module"

    # Execution errors
    EXECUTION_ERROR = "execution_error"
    STAGE_FAILED = "stage_failed"
    PIPELINE_ABORTED = "pipeline_aborted"

    # Provider errors
    PROVIDER_ERROR = "provider_error"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_AUTHENTICATION_FAILED = "provider_authentication_failed"

    # Infrastructure errors
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    QUOTA_EXCEEDED = "quota_exceeded"

    # Authorization
    PERMISSION_DENIED = "permission_denied"
    WORKSPACE_NOT_FOUND = "workspace_not_found"
    USER_NOT_AUTHORIZED = "user_not_authorized"

    # Dependencies
    DEPENDENCY_ERROR = "dependency_error"
    MODULE_NOT_REGISTERED = "module_not_registered"
    KNOWLEDGE_SOURCE_UNAVAILABLE = "knowledge_source_unavailable"

    # Generic
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(str, Enum):
    """How critical the error is to the caller."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Structured error models
# ---------------------------------------------------------------------------


class FieldValidationError(BaseModel):
    """A single field-level validation failure."""

    field: str
    message: str
    provided_value: Optional[Any] = None


class IntelligenceError(BaseModel):
    """Canonical error payload included in ``IntelligenceResponse.errors``.

    This model is also the body of HTTP 4xx / 5xx error responses so
    PJ's backend can forward them to Tejus's frontend as-is.
    """

    error_id: str = Field(default_factory=lambda: f"err-{uuid.uuid4().hex[:8]}")
    code: ErrorCode
    severity: ErrorSeverity = ErrorSeverity.ERROR
    message: str
    detail: str = ""
    field_errors: List[FieldValidationError] = Field(default_factory=list)
    request_id: Optional[str] = None
    execution_id: Optional[str] = None
    module: Optional[str] = None
    retryable: bool = False
    retry_after_seconds: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    context: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Error response envelope
# ---------------------------------------------------------------------------


class IntelligenceErrorResponse(BaseModel):
    """Top-level HTTP error envelope — returned instead of ``IntelligenceResponse`` on failure."""

    request_id: str
    error: IntelligenceError
    http_status: int = 500            # mirrors the HTTP status code sent to the caller
