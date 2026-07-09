"""OpenAPI 3.1 specification generator for the Intelligence API contracts.

Generates a complete OpenAPI 3.1 document from the contract models so
that PJ's backend can serve it at ``GET /openapi.json``, Tejus's frontend
can import it into a type generator, and the SDK can scaffold client code.

Usage
-----
>>> from backend.intelligence.contracts.openapi_generator import OpenAPIGenerator
>>> spec = OpenAPIGenerator.generate()
>>> import json; print(json.dumps(spec, indent=2))
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.intelligence.contracts.schemas import get_all_schemas


class OpenAPIGenerator:
    """Generates an OpenAPI 3.1 specification from registered contract schemas.

    The generator is intentionally minimal: it produces a ``components/schemas``
    section from all Pydantic models and pre-defines the standard endpoint
    shapes for the three core operations (analyse, stream, compare).
    """

    API_VERSION: str = "1.0.0"
    API_TITLE: str = "Nexus AI Intelligence API"
    API_DESCRIPTION: str = (
        "Official contract specification for the Nexus AI Intelligence Framework. "
        "Consumed by the platform backend, frontend, and Developer SDK."
    )

    @classmethod
    def generate(cls) -> Dict[str, Any]:
        """Generates the full OpenAPI 3.1 document.

        Returns:
            A JSON-serialisable dict conforming to the OpenAPI 3.1 spec.
        """
        schemas = cls._build_component_schemas()
        paths = cls._build_paths()

        return {
            "openapi": "3.1.0",
            "info": {
                "title": cls.API_TITLE,
                "version": cls.API_VERSION,
                "description": cls.API_DESCRIPTION,
                "contact": {
                    "name": "Nexus AI Platform Team",
                    "email": "platform@nexus.ai",
                },
            },
            "servers": [
                {"url": "https://api.nexus.ai/v1", "description": "Production"},
                {"url": "https://staging.api.nexus.ai/v1", "description": "Staging"},
                {"url": "http://localhost:8000/v1", "description": "Local development"},
            ],
            "components": {
                "schemas": schemas,
                "securitySchemes": {
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                    }
                },
            },
            "security": [{"BearerAuth": []}],
            "paths": paths,
            "tags": [
                {"name": "intelligence", "description": "Core intelligence analysis operations"},
                {"name": "streaming", "description": "Streaming / SSE endpoints"},
            ],
        }

    @classmethod
    def generate_json(cls, indent: int = 2) -> str:
        """Returns the OpenAPI spec as a pretty-printed JSON string."""
        return json.dumps(cls.generate(), indent=indent)

    @classmethod
    def generate_sdk_models(cls) -> Dict[str, Any]:
        """Returns a simplified dict suitable for SDK code-generation tools.

        The output maps model name → field list (name, type, required flag)
        to assist language-specific SDK scaffolding.

        Returns:
            Dict mapping model_name → list of field descriptors.
        """
        sdk_models: Dict[str, Any] = {}
        all_schemas = get_all_schemas()

        for name, schema in all_schemas.items():
            fields = []
            properties = schema.get("properties", {})
            required = set(schema.get("required", []))
            for field_name, field_schema in properties.items():
                fields.append({
                    "name": field_name,
                    "type": field_schema.get("type", "any"),
                    "required": field_name in required,
                    "description": field_schema.get("description", ""),
                    "default": field_schema.get("default"),
                })
            sdk_models[name] = {"fields": fields}

        return sdk_models

    # ------------------------------------------------------------------
    # Private builders
    # ------------------------------------------------------------------

    @classmethod
    def _build_component_schemas(cls) -> Dict[str, Any]:
        """Converts all registered JSON Schemas into OpenAPI component schemas."""
        all_schemas = get_all_schemas()
        # OpenAPI 3.1 is a superset of JSON Schema Draft 2020-12; schemas are valid as-is.
        return {name: schema for name, schema in all_schemas.items()}

    @classmethod
    def _build_paths(cls) -> Dict[str, Any]:
        """Defines the standard endpoint paths for the Intelligence API."""

        def _ref(model_name: str) -> Dict[str, str]:
            return {"$ref": f"#/components/schemas/{model_name}"}

        def _json_body(model_name: str) -> Dict[str, Any]:
            return {
                "required": True,
                "content": {"application/json": {"schema": _ref(model_name)}},
            }

        def _json_response(model_name: str, description: str) -> Dict[str, Any]:
            return {
                "description": description,
                "content": {"application/json": {"schema": _ref(model_name)}},
            }

        def _error_responses() -> Dict[str, Any]:
            return {
                "400": _json_response("IntelligenceErrorResponse", "Validation error"),
                "403": _json_response("IntelligenceErrorResponse", "Permission denied"),
                "404": _json_response("IntelligenceErrorResponse", "Module not found"),
                "429": _json_response("IntelligenceErrorResponse", "Rate limit exceeded"),
                "500": _json_response("IntelligenceErrorResponse", "Internal execution error"),
                "504": _json_response("IntelligenceErrorResponse", "Execution timeout"),
            }

        return {
            "/intelligence/analyse": {
                "post": {
                    "operationId": "analyseIntelligence",
                    "summary": "Run an intelligence analysis",
                    "description": (
                        "Accepts a standard IntelligenceRequest and executes the "
                        "named intelligence module. Returns IntelligenceResponse."
                    ),
                    "tags": ["intelligence"],
                    "requestBody": _json_body("IntelligenceRequest"),
                    "responses": {
                        "200": _json_response("IntelligenceResponse", "Analysis completed"),
                        **_error_responses(),
                    },
                }
            },
            "/intelligence/stream": {
                "post": {
                    "operationId": "streamIntelligence",
                    "summary": "Stream an intelligence analysis",
                    "description": (
                        "Identical to /analyse but returns a Server-Sent Events "
                        "stream of StreamProgressEvent, StreamTokenEvent, and "
                        "StreamCompletionEvent objects."
                    ),
                    "tags": ["streaming"],
                    "requestBody": _json_body("IntelligenceRequest"),
                    "responses": {
                        "200": {
                            "description": "SSE stream",
                            "content": {
                                "text/event-stream": {
                                    "schema": {
                                        "oneOf": [
                                            _ref("StreamProgressEvent"),
                                            _ref("StreamTokenEvent"),
                                            _ref("StreamCompletionEvent"),
                                            _ref("StreamCancellationEvent"),
                                            _ref("StreamErrorEvent"),
                                        ]
                                    }
                                }
                            },
                        },
                        **_error_responses(),
                    },
                }
            },
            "/intelligence/sessions/{stream_id}/cancel": {
                "post": {
                    "operationId": "cancelStream",
                    "summary": "Cancel a streaming session",
                    "tags": ["streaming"],
                    "parameters": [
                        {
                            "name": "stream_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": _json_response("StreamCancellationEvent", "Cancellation acknowledged"),
                        **_error_responses(),
                    },
                }
            },
            "/intelligence/schemas": {
                "get": {
                    "operationId": "listSchemas",
                    "summary": "List all contract schema names",
                    "tags": ["intelligence"],
                    "responses": {
                        "200": {
                            "description": "Schema names",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
        }
