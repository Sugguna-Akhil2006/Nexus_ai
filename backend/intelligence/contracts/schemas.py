"""JSON Schema definitions for all intelligence contract models.

Generates stable schema objects that ``openapi_generator.py`` consumes
to build the full OpenAPI spec.  Each schema is a plain ``dict`` that
conforms to JSON Schema Draft 7 / OpenAPI 3.1 Component format.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.intelligence.contracts.error_models import (
    IntelligenceError,
    IntelligenceErrorResponse,
)
from backend.intelligence.contracts.request_models import (
    Attachment,
    IntelligenceRequest,
    RequestMetadata,
    RequestOptions,
)
from backend.intelligence.contracts.response_models import (
    Artifact,
    Citation,
    ExecutionMetrics,
    IntelligenceResponse,
    Recommendation,
)
from backend.intelligence.contracts.streaming_models import (
    StreamCancellationEvent,
    StreamCompletionEvent,
    StreamErrorEvent,
    StreamPartialResponseEvent,
    StreamProgressEvent,
    StreamSession,
    StreamTokenEvent,
)


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------


_MODELS = {
    # Request side
    "IntelligenceRequest": IntelligenceRequest,
    "RequestOptions": RequestOptions,
    "RequestMetadata": RequestMetadata,
    "Attachment": Attachment,
    # Response side
    "IntelligenceResponse": IntelligenceResponse,
    "ExecutionMetrics": ExecutionMetrics,
    "Citation": Citation,
    "Artifact": Artifact,
    "Recommendation": Recommendation,
    # Error side
    "IntelligenceError": IntelligenceError,
    "IntelligenceErrorResponse": IntelligenceErrorResponse,
    # Streaming
    "StreamSession": StreamSession,
    "StreamProgressEvent": StreamProgressEvent,
    "StreamPartialResponseEvent": StreamPartialResponseEvent,
    "StreamTokenEvent": StreamTokenEvent,
    "StreamCompletionEvent": StreamCompletionEvent,
    "StreamCancellationEvent": StreamCancellationEvent,
    "StreamErrorEvent": StreamErrorEvent,
}


def get_json_schema(model_name: str) -> Dict[str, Any]:
    """Returns the JSON Schema dict for a named contract model.

    Args:
        model_name: Key from the schema registry (e.g. "IntelligenceRequest").

    Returns:
        JSON Schema dict.

    Raises:
        KeyError: If the model_name is not registered.
    """
    if model_name not in _MODELS:
        raise KeyError(
            f"'{model_name}' is not a registered contract schema. "
            f"Available: {sorted(_MODELS.keys())}"
        )
    return _MODELS[model_name].model_json_schema()


def get_all_schemas() -> Dict[str, Dict[str, Any]]:
    """Returns JSON Schemas for every registered contract model.

    Returns:
        Mapping of model_name → JSON Schema dict.
    """
    return {name: model.model_json_schema() for name, model in _MODELS.items()}


def list_schema_names() -> list[str]:
    """Returns a sorted list of all registered contract model names."""
    return sorted(_MODELS.keys())
