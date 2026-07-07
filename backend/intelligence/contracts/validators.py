"""Input / output validation layer for the Intelligence API contracts.

Validates ``IntelligenceRequest`` payloads, attachment metadata, and
``IntelligenceResponse`` structured outputs before they reach module
execution or are returned to callers.  All functions are stateless and
side-effect-free — no EventBus, no I/O.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from backend.intelligence.contracts.error_models import (
    ErrorCode,
    ErrorSeverity,
    FieldValidationError,
    IntelligenceError,
)
from backend.intelligence.contracts.request_models import (
    Attachment,
    AttachmentType,
    IntelligenceModule,
    IntelligenceRequest,
)
from backend.intelligence.contracts.response_models import (
    IntelligenceResponse,
    ResponseStatus,
)


# ---------------------------------------------------------------------------
# Validation results
# ---------------------------------------------------------------------------


class ValidationResult:
    """Holds the outcome of a validation pass.

    Attributes:
        valid:   ``True`` if all checks passed.
        errors:  List of ``IntelligenceError`` objects describing failures.
    """

    def __init__(self) -> None:
        self.valid: bool = True
        self.errors: List[IntelligenceError] = []

    def add_error(self, code: ErrorCode, message: str, field: str = "") -> None:
        """Records a validation failure and marks the result invalid."""
        self.valid = False
        field_errors = [FieldValidationError(field=field, message=message)] if field else []
        self.errors.append(IntelligenceError(
            code=code,
            severity=ErrorSeverity.ERROR,
            message=message,
            field_errors=field_errors,
        ))


# ---------------------------------------------------------------------------
# Request validators
# ---------------------------------------------------------------------------


def validate_request(request: IntelligenceRequest) -> ValidationResult:
    """Runs the full validation suite on an ``IntelligenceRequest``.

    Checks:
    - Required identity fields are non-empty.
    - ``module`` is a known ``IntelligenceModule`` value.
    - ``input`` dict is not empty.
    - Each attachment satisfies ``validate_attachment()``.
    - ``options.temperature`` is in [0.0, 2.0].
    - ``options.timeout_seconds`` is positive.

    Args:
        request: The request to validate.

    Returns:
        A ``ValidationResult`` with ``valid=True`` or accumulated errors.
    """
    result = ValidationResult()

    # Identity checks (belt-and-suspenders on top of Pydantic validators)
    if not request.workspace_id:
        result.add_error(ErrorCode.MISSING_FIELD, "workspace_id is required.", "workspace_id")
    if not request.user_id:
        result.add_error(ErrorCode.MISSING_FIELD, "user_id is required.", "user_id")

    # Module validation
    try:
        IntelligenceModule(request.module.value)
    except ValueError:
        result.add_error(
            ErrorCode.INVALID_MODULE,
            f"'{request.module}' is not a registered intelligence module.",
            "module",
        )

    # Input must carry at least one key
    if not request.input:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            "Request 'input' must contain at least one field.",
            "input",
        )

    # Options range checks
    if not (0.0 <= request.options.temperature <= 2.0):
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            f"options.temperature must be in [0.0, 2.0], got {request.options.temperature}.",
            "options.temperature",
        )
    if request.options.timeout_seconds <= 0:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            "options.timeout_seconds must be a positive integer.",
            "options.timeout_seconds",
        )

    # Validate each attachment
    for att in request.attachments:
        att_result = validate_attachment(att)
        if not att_result.valid:
            result.valid = False
            result.errors.extend(att_result.errors)

    return result


def validate_attachment(attachment: Attachment) -> ValidationResult:
    """Validates a single request attachment.

    Args:
        attachment: The ``Attachment`` to validate.

    Returns:
        ``ValidationResult`` indicating whether the attachment is usable.
    """
    result = ValidationResult()
    if not attachment.name:
        result.add_error(ErrorCode.MISSING_FIELD, "Attachment name is required.", "attachment.name")

    url_types = {AttachmentType.URL}
    requires_content = attachment.attachment_type not in url_types

    if requires_content and not attachment.content_base64 and not attachment.url:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            f"Attachment '{attachment.name}' must provide content_base64 or url.",
            "attachment.content_base64",
        )
    if attachment.attachment_type == AttachmentType.URL and not attachment.url:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            f"URL attachment '{attachment.name}' must provide a url.",
            "attachment.url",
        )
    return result


# ---------------------------------------------------------------------------
# Response validators
# ---------------------------------------------------------------------------


def validate_response(response: IntelligenceResponse) -> ValidationResult:
    """Validates that a module-produced ``IntelligenceResponse`` satisfies the contract.

    Args:
        response: The response to validate.

    Returns:
        ``ValidationResult`` indicating contract compliance.
    """
    result = ValidationResult()

    if not response.execution_id:
        result.add_error(ErrorCode.MISSING_FIELD, "Response must include execution_id.", "execution_id")
    if not response.request_id:
        result.add_error(ErrorCode.MISSING_FIELD, "Response must include request_id.", "request_id")
    if not (0.0 <= response.confidence <= 1.0):
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            f"Response confidence {response.confidence} must be in [0.0, 1.0].",
            "confidence",
        )
    if response.status == ResponseStatus.COMPLETED and not response.summary:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            "Completed responses must include a non-empty summary.",
            "summary",
        )
    return result


# ---------------------------------------------------------------------------
# Metadata / artifact validators
# ---------------------------------------------------------------------------


def validate_metadata(metadata: Dict[str, Any]) -> ValidationResult:
    """Validates that a free-form metadata dict does not exceed limits.

    Args:
        metadata: Caller-supplied metadata dict.

    Returns:
        ``ValidationResult``.
    """
    result = ValidationResult()
    if len(metadata) > 50:
        result.add_error(
            ErrorCode.VALIDATION_ERROR,
            f"Metadata may contain at most 50 keys; got {len(metadata)}.",
            "metadata",
        )
    for key in metadata:
        if not isinstance(key, str) or not key.strip():
            result.add_error(
                ErrorCode.VALIDATION_ERROR,
                f"Metadata key '{key}' must be a non-empty string.",
                "metadata",
            )
            break
    return result
