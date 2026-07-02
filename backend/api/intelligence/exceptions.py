"""Gateway-specific exceptions mapping errors to HTTP status codes."""

from fastapi import HTTPException, status


class GatewayException(HTTPException):
    """Base exception for Gateway routing and processing errors."""


class ModuleNotFoundError(GatewayException):
    """Raised when no registered module matches a capability."""
    def __init__(self, capability: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registered module supports capability: '{capability}'."
        )


class GatewayValidationError(GatewayException):
    """Raised when validation check fails on request parameters."""
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
