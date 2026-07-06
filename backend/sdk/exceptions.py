"""Standardized SDK exception hierarchy for Nexus AI public API clients."""

from __future__ import annotations

from typing import Any, Dict, Optional


class NexusSDKError(Exception):
    """Base exception for all Nexus AI SDK errors.

    Attributes:
        message: Human-readable error description.
        status_code: HTTP status code when applicable.
        error_code: Machine-readable error code from the API.
        details: Additional error context from the server.
        correlation_id: Request correlation identifier.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.correlation_id = correlation_id


class ValidationError(NexusSDKError):
    """Raised when request parameters fail validation (HTTP 400)."""


class AuthenticationError(NexusSDKError):
    """Raised when authentication credentials are missing or invalid (HTTP 401)."""


class RateLimitError(NexusSDKError):
    """Raised when the API rate limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, when provided.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("status_code", None)
        kwargs.pop("error_code", None)
        super().__init__(message, status_code=429, error_code="RATE_LIMIT_EXCEEDED", **kwargs)
        self.retry_after = retry_after


class ExecutionError(NexusSDKError):
    """Raised when an intelligence execution fails (HTTP 422/500)."""


class ProviderError(NexusSDKError):
    """Raised when an upstream model or provider fails (HTTP 502/503)."""


def map_status_to_exception(
    status_code: int,
    body: Dict[str, Any],
    correlation_id: Optional[str] = None,
) -> NexusSDKError:
    """Maps an HTTP status code and response body to the appropriate SDK exception.

    Args:
        status_code: HTTP response status code.
        body: Parsed JSON response body.
        correlation_id: Optional request correlation ID.

    Returns:
        A typed NexusSDKError subclass instance.
    """
    message = body.get("message") or body.get("detail") or "Unknown API error"
    error_code = body.get("error_code")
    details = body.get("details") or {}

    if isinstance(message, list):
        message = str(message)

    common = {
        "status_code": status_code,
        "error_code": error_code,
        "details": details if isinstance(details, dict) else {"raw": details},
        "correlation_id": correlation_id or body.get("correlation_id"),
    }

    if status_code == 400:
        return ValidationError(str(message), **common)
    if status_code == 401:
        return AuthenticationError(str(message), **common)
    if status_code == 429:
        retry_after = None
        if isinstance(details, dict):
            retry_after = details.get("retry_after_seconds")
        return RateLimitError(str(message), retry_after=retry_after, **common)
    if status_code in (502, 503):
        return ProviderError(str(message), **common)
    if status_code >= 500 or status_code == 422:
        return ExecutionError(str(message), **common)
    return NexusSDKError(str(message), **common)
