"""Unified response serialization for the Product Experience Layer.

Provides typed generic wrappers ensuring a consistent JSON envelope across
all product API endpoints, plus convenience helpers for converting domain
report objects into serializable dictionaries.

Types
-----
- ProductResponse[T]   : Single-item success/error envelope.
- PaginatedResponse[T] : Paginated list envelope with navigation metadata.
- ErrorResponse        : Structured error payload.
- serialize_report     : Domain-agnostic report serializer.
- serialize_history    : History list serializer.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Core Response Models
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Additional structured context for an error response.

    Attributes:
        field: Optional field name that caused the error.
        reason: Human-readable explanation.
        code: Machine-readable error sub-code.
    """

    field: Optional[str] = None
    reason: str
    code: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardised error envelope returned by all product endpoints.

    Attributes:
        success: Always False for error responses.
        error_code: HTTP-level or domain error code string.
        message: User-facing error message.
        details: Optional list of per-field or sub-error details.
        request_id: Echo of the originating request ID.
        timestamp: UTC timestamp of the error.
    """

    success: bool = False
    error_code: str
    message: str
    details: List[ErrorDetail] = Field(default_factory=list)
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductResponse(GenericModel, Generic[T]):
    """Generic success envelope wrapping any product data payload.

    Attributes:
        success: True when the operation completed without error.
        data: The response payload (typed via generic parameter T).
        message: Optional human-readable status message.
        request_id: Unique identifier for tracing this response.
        timestamp: UTC timestamp of the response generation.
        duration_ms: Optional processing duration in milliseconds.
    """

    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[float] = None

    @classmethod
    def ok(
        cls,
        data: T,
        message: Optional[str] = None,
        duration_ms: Optional[float] = None,
    ) -> "ProductResponse[T]":
        """Factory method for successful responses.

        Args:
            data: The response payload.
            message: Optional status message.
            duration_ms: Optional processing duration.

        Returns:
            A populated ProductResponse with success=True.
        """
        return cls(success=True, data=data, message=message, duration_ms=duration_ms)

    @classmethod
    def fail(
        cls,
        message: str,
        request_id: Optional[str] = None,
    ) -> "ProductResponse[None]":
        """Factory method for failed responses without data.

        Args:
            message: Reason for failure.
            request_id: Optional request ID for correlation.

        Returns:
            A ProductResponse with success=False and no data.
        """
        return cls(
            success=False,
            data=None,
            message=message,
            request_id=request_id or str(uuid.uuid4()),
        )


class PaginatedResponse(GenericModel, Generic[T]):
    """Generic paginated list envelope.

    Attributes:
        success: Always True for paginated responses.
        items: The current page's data items.
        total: Total item count across all pages.
        page: Current (1-indexed) page number.
        page_size: Number of items per page.
        has_next: Whether a subsequent page exists.
        has_prev: Whether a preceding page exists.
        request_id: Unique request identifier.
        timestamp: UTC timestamp of response generation.
    """

    success: bool = True
    items: List[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False
    has_prev: bool = False
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_list(
        cls,
        items: List[T],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse[T]":
        """Builds a paginated response from a pre-sliced item list.

        Args:
            items: The items for the current page.
            total: Total number of items across all pages.
            page: Current page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            A fully populated PaginatedResponse.
        """
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        )


# ---------------------------------------------------------------------------
# Domain Report Serializers
# ---------------------------------------------------------------------------


def serialize_report(report: Any) -> Dict[str, Any]:
    """Serializes any Pydantic-based domain report to a plain dictionary.

    Handles Resume (ProductResumeReport), GitHub (GitHubIntelligenceReport),
    and Document (DocumentKnowledgeReport) reports via duck-typed model_dump.

    Args:
        report: A Pydantic model instance from any intelligence domain.

    Returns:
        Dict containing the serialized report fields.

    Raises:
        ValueError: If the object does not expose a model_dump method.
    """
    if hasattr(report, "model_dump"):
        return report.model_dump()
    if hasattr(report, "dict"):
        return report.dict()
    raise ValueError(
        f"Cannot serialize report of type {type(report).__name__}. "
        "Expected a Pydantic BaseModel subclass."
    )


def serialize_report_json(report: Any) -> str:
    """Serializes any Pydantic-based domain report to a JSON string.

    Args:
        report: A Pydantic model instance from any intelligence domain.

    Returns:
        JSON-formatted string.

    Raises:
        ValueError: If the object does not expose a model_dump_json method.
    """
    if hasattr(report, "model_dump_json"):
        return report.model_dump_json()
    import json
    return json.dumps(serialize_report(report), default=str)


def serialize_history(records: List[Any]) -> List[Dict[str, Any]]:
    """Serializes a list of HistoryRecord or domain report objects.

    Args:
        records: List of Pydantic model instances.

    Returns:
        List of serialized dictionaries, skipping any failures gracefully.
    """
    result: List[Dict[str, Any]] = []
    for record in records:
        try:
            result.append(serialize_report(record))
        except Exception:
            pass
    return result


def paginate(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Applies in-memory pagination to a list and returns a slice with metadata.

    Args:
        items: Full item list to paginate.
        page: Requested page number (1-indexed).
        page_size: Items per page.

    Returns:
        Dictionary with 'items', 'total', 'page', 'page_size', 'has_next', 'has_prev'.
    """
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": end < total,
        "has_prev": page > 1,
    }
