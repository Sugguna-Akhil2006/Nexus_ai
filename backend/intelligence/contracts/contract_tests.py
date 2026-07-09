"""Comprehensive contract tests for the Intelligence API.

Covers:
- Contract (schema structure) tests
- Backward compatibility tests
- Serialization / deserialization round-trip tests
- Streaming model tests
- Schema validation tests
- OpenAPI generation tests
"""

from __future__ import annotations

import json
import unittest
from datetime import datetime

from backend.intelligence.contracts.error_models import (
    ErrorCode,
    ErrorSeverity,
    FieldValidationError,
    IntelligenceError,
    IntelligenceErrorResponse,
)
from backend.intelligence.contracts.events import (
    AnalysisCompletedPayload,
    AnalysisEventPublisher,
    AnalysisFailedPayload,
    AnalysisProgressPayload,
    AnalysisStartedPayload,
)
from backend.intelligence.contracts.openapi_generator import OpenAPIGenerator
from backend.intelligence.contracts.request_models import (
    Attachment,
    AttachmentType,
    IntelligenceModule,
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
    ResponseStatus,
)
from backend.intelligence.contracts.schemas import (
    get_all_schemas,
    get_json_schema,
    list_schema_names,
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
from backend.intelligence.contracts.validators import (
    ValidationResult,
    validate_attachment,
    validate_metadata,
    validate_request,
    validate_response,
)
from backend.runtime.event import EventBus, EventType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reset_bus() -> None:
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {
            "published_count": 0,
            "dispatched_count": 0,
            "failed_count": 0,
            "by_type": {},
        }


def _make_request(**kwargs) -> IntelligenceRequest:
    defaults = dict(
        workspace_id="ws-test",
        user_id="user-001",
        module=IntelligenceModule.RESUME,
        input={"text": "Sample resume content"},
    )
    defaults.update(kwargs)
    return IntelligenceRequest(**defaults)


def _make_response(**kwargs) -> IntelligenceResponse:
    defaults = dict(
        execution_id="exec-test",
        request_id="req-test",
        module=IntelligenceModule.RESUME.value,
        status=ResponseStatus.COMPLETED,
        confidence=0.88,
        summary="Analysis complete.",
    )
    defaults.update(kwargs)
    return IntelligenceResponse(**defaults)


# ===========================================================================
# Contract / schema structure tests
# ===========================================================================

class TestContractStructure(unittest.TestCase):
    """Validates that every model exposes its required fields."""

    def test_request_required_fields(self) -> None:
        req = _make_request()
        self.assertTrue(req.request_id.startswith("req-"))
        self.assertEqual(req.workspace_id, "ws-test")
        self.assertEqual(req.user_id, "user-001")
        self.assertEqual(req.module, IntelligenceModule.RESUME)
        self.assertIsInstance(req.options, RequestOptions)
        self.assertIsInstance(req.metadata, RequestMetadata)

    def test_response_required_fields(self) -> None:
        resp = _make_response()
        self.assertTrue(resp.execution_id)
        self.assertIsInstance(resp.execution_metrics, ExecutionMetrics)
        self.assertIsInstance(resp.citations, list)
        self.assertIsInstance(resp.artifacts, list)
        self.assertIsInstance(resp.recommendations, list)

    def test_all_modules_are_registered(self) -> None:
        """Every IntelligenceModule enum value must be constructable as a request module."""
        for module in IntelligenceModule:
            req = _make_request(module=module)
            self.assertEqual(req.module, module)

    def test_error_model_structure(self) -> None:
        err = IntelligenceError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Bad input",
            field_errors=[FieldValidationError(field="input", message="must not be empty")],
        )
        self.assertEqual(err.code, ErrorCode.VALIDATION_ERROR)
        self.assertEqual(len(err.field_errors), 1)
        self.assertFalse(err.retryable)

    def test_error_response_envelope(self) -> None:
        inner = IntelligenceError(code=ErrorCode.TIMEOUT, message="Timed out", retryable=True)
        env = IntelligenceErrorResponse(request_id="req-xyz", error=inner, http_status=504)
        self.assertEqual(env.http_status, 504)
        self.assertTrue(env.error.retryable)


# ===========================================================================
# Backward compatibility tests
# ===========================================================================

class TestBackwardCompatibility(unittest.TestCase):
    """Ensures that new optional fields do not break existing serialized payloads."""

    _LEGACY_REQUEST_JSON = json.dumps({
        "workspace_id": "ws-legacy",
        "user_id": "user-legacy",
        "module": "resume",
        "input": {"text": "legacy content"},
    })

    _LEGACY_RESPONSE_JSON = json.dumps({
        "execution_id": "exec-legacy",
        "request_id": "req-legacy",
        "module": "resume",
        "status": "completed",
    })

    def test_legacy_request_deserializes(self) -> None:
        """Old payloads missing optional fields must still be valid."""
        req = IntelligenceRequest.model_validate_json(self._LEGACY_REQUEST_JSON)
        self.assertEqual(req.workspace_id, "ws-legacy")
        self.assertIsNotNone(req.options)           # default-injected
        self.assertIsNotNone(req.metadata)          # default-injected
        self.assertEqual(req.attachments, [])

    def test_legacy_response_deserializes(self) -> None:
        resp = IntelligenceResponse.model_validate_json(self._LEGACY_RESPONSE_JSON)
        self.assertEqual(resp.status, ResponseStatus.COMPLETED)
        self.assertEqual(resp.confidence, 0.0)      # default
        self.assertEqual(resp.summary, "")

    def test_extra_fields_ignored(self) -> None:
        """Future fields added by a newer server must not break old clients."""
        payload = {
            "workspace_id": "ws-x",
            "user_id": "u-x",
            "module": "github",
            "input": {"repo": "nexus"},
            "_future_field": "ignored",
        }
        # Pydantic v2 default: extra fields are ignored
        req = IntelligenceRequest.model_validate(payload)
        self.assertEqual(req.module, IntelligenceModule.GITHUB)


# ===========================================================================
# Serialization tests
# ===========================================================================

class TestSerialization(unittest.TestCase):
    """Validates full round-trip JSON serialization/deserialization."""

    def test_request_round_trip(self) -> None:
        req = _make_request(
            attachments=[
                Attachment(
                    name="resume.pdf",
                    attachment_type=AttachmentType.PDF,
                    content_base64="dGVzdA==",
                )
            ],
            options=RequestOptions(stream=True, max_tokens=500, language="fr"),
        )
        serialized = req.model_dump_json()
        restored = IntelligenceRequest.model_validate_json(serialized)
        self.assertEqual(restored.request_id, req.request_id)
        self.assertEqual(len(restored.attachments), 1)
        self.assertTrue(restored.options.stream)
        self.assertEqual(restored.options.language, "fr")

    def test_response_round_trip(self) -> None:
        resp = _make_response(
            artifacts=[Artifact(artifact_type="report", name="full_report", content={"score": 9})],
            citations=[Citation(source_type="document", identifier="doc-1", title="CV Guide")],
            recommendations=[
                Recommendation(category="skills", title="Add Python", description="Mention Python")
            ],
        )
        serialized = resp.model_dump_json()
        restored = IntelligenceResponse.model_validate_json(serialized)
        self.assertEqual(len(restored.artifacts), 1)
        self.assertEqual(len(restored.citations), 1)
        self.assertEqual(len(restored.recommendations), 1)
        self.assertEqual(restored.citations[0].title, "CV Guide")

    def test_error_round_trip(self) -> None:
        err = IntelligenceError(
            code=ErrorCode.PROVIDER_ERROR,
            message="LLM provider returned 503",
            retryable=True,
            retry_after_seconds=30,
        )
        payload = json.loads(err.model_dump_json())
        self.assertEqual(payload["code"], "provider_error")
        self.assertTrue(payload["retryable"])
        self.assertEqual(payload["retry_after_seconds"], 30)


# ===========================================================================
# Streaming model tests
# ===========================================================================

class TestStreamingModels(unittest.TestCase):
    """Validates all streaming event models."""

    def test_stream_session_auto_id(self) -> None:
        sess = StreamSession(request_id="req-s1", module="resume")
        self.assertTrue(sess.stream_id.startswith("stream-"))
        self.assertFalse(sess.cancelled)
        self.assertFalse(sess.completed)

    def test_progress_event(self) -> None:
        ev = StreamProgressEvent(
            stream_id="stream-1", request_id="req-1",
            stage="parsing", percent_complete=33.0, message="Parsing PDF"
        )
        self.assertEqual(ev.percent_complete, 33.0)

    def test_token_event(self) -> None:
        ev = StreamTokenEvent(
            stream_id="stream-1", request_id="req-1", token="Hello", cumulative_tokens=5
        )
        self.assertEqual(ev.token, "Hello")

    def test_partial_response_event(self) -> None:
        ev = StreamPartialResponseEvent(
            stream_id="stream-1", request_id="req-1",
            partial_output={"section": "skills", "data": ["Python"]},
            is_final=False,
        )
        self.assertFalse(ev.is_final)
        self.assertIn("skills", ev.partial_output["section"])

    def test_completion_event(self) -> None:
        ev = StreamCompletionEvent(
            stream_id="stream-1", request_id="req-1",
            execution_id="exec-1", total_tokens=800, duration_ms=1200.0, final_confidence=0.91
        )
        self.assertAlmostEqual(ev.final_confidence, 0.91)

    def test_cancellation_event(self) -> None:
        ev = StreamCancellationEvent(
            stream_id="stream-1", request_id="req-1", reason="user_cancelled"
        )
        self.assertEqual(ev.reason, "user_cancelled")

    def test_error_event(self) -> None:
        ev = StreamErrorEvent(
            stream_id="stream-1", request_id="req-1",
            error_code="provider_error", message="Model overloaded"
        )
        self.assertFalse(ev.recoverable)

    def test_all_event_kinds_round_trip(self) -> None:
        """All streaming events must be JSON round-trippable."""
        events = [
            StreamProgressEvent(stream_id="s", request_id="r", stage="s1", percent_complete=10),
            StreamTokenEvent(stream_id="s", request_id="r", token="tok"),
            StreamPartialResponseEvent(stream_id="s", request_id="r", partial_output={"k": "v"}),
            StreamCompletionEvent(stream_id="s", request_id="r", execution_id="e"),
            StreamCancellationEvent(stream_id="s", request_id="r"),
            StreamErrorEvent(stream_id="s", request_id="r", error_code="e", message="m"),
        ]
        for ev in events:
            restored = type(ev).model_validate_json(ev.model_dump_json())
            self.assertEqual(restored.stream_id, "s")


# ===========================================================================
# Schema validation tests
# ===========================================================================

class TestSchemaValidation(unittest.TestCase):
    """Validates the schema registry and the validator utilities."""

    def test_all_schemas_registered(self) -> None:
        names = list_schema_names()
        self.assertGreaterEqual(len(names), 10)
        self.assertIn("IntelligenceRequest", names)
        self.assertIn("IntelligenceResponse", names)
        self.assertIn("IntelligenceError", names)

    def test_get_schema_by_name(self) -> None:
        schema = get_json_schema("IntelligenceRequest")
        self.assertIn("properties", schema)
        self.assertIn("workspace_id", schema["properties"])

    def test_unknown_schema_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_json_schema("NonExistentModel")

    def test_valid_request_passes_validation(self) -> None:
        result = validate_request(_make_request())
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_empty_workspace_fails(self) -> None:
        from pydantic import ValidationError as PydanticError
        with self.assertRaises(PydanticError):
            IntelligenceRequest(
                workspace_id="",
                user_id="u1",
                module=IntelligenceModule.RESUME,
                input={"text": "x"},
            )

    def test_empty_input_fails_validation(self) -> None:
        req = _make_request()
        req.input = {}
        result = validate_request(req)
        self.assertFalse(result.valid)
        self.assertTrue(any(e.code == ErrorCode.VALIDATION_ERROR for e in result.errors))

    def test_invalid_temperature_fails(self) -> None:
        req = _make_request()
        req.options.temperature = 5.0
        result = validate_request(req)
        self.assertFalse(result.valid)

    def test_valid_attachment_passes(self) -> None:
        att = Attachment(
            name="cv.pdf",
            attachment_type=AttachmentType.PDF,
            content_base64="dGVzdA==",
        )
        result = validate_attachment(att)
        self.assertTrue(result.valid)

    def test_url_attachment_without_url_fails(self) -> None:
        att = Attachment(name="link", attachment_type=AttachmentType.URL)
        result = validate_attachment(att)
        self.assertFalse(result.valid)

    def test_valid_response_passes(self) -> None:
        result = validate_response(_make_response())
        self.assertTrue(result.valid)

    def test_response_without_summary_fails(self) -> None:
        resp = _make_response(summary="")
        result = validate_response(resp)
        self.assertFalse(result.valid)

    def test_metadata_too_many_keys(self) -> None:
        big_meta = {f"k{i}": i for i in range(60)}
        result = validate_metadata(big_meta)
        self.assertFalse(result.valid)

    def test_metadata_small_passes(self) -> None:
        result = validate_metadata({"source": "sdk", "version": "2"})
        self.assertTrue(result.valid)


# ===========================================================================
# OpenAPI generation tests
# ===========================================================================

class TestOpenAPIGeneration(unittest.TestCase):
    """Validates the OpenAPI 3.1 document structure."""

    def setUp(self) -> None:
        self.spec = OpenAPIGenerator.generate()

    def test_openapi_version(self) -> None:
        self.assertEqual(self.spec["openapi"], "3.1.0")

    def test_info_block(self) -> None:
        self.assertIn("title", self.spec["info"])
        self.assertIn("version", self.spec["info"])

    def test_components_schemas_present(self) -> None:
        schemas = self.spec["components"]["schemas"]
        self.assertIn("IntelligenceRequest", schemas)
        self.assertIn("IntelligenceResponse", schemas)
        self.assertIn("IntelligenceError", schemas)
        self.assertIn("StreamCompletionEvent", schemas)

    def test_paths_defined(self) -> None:
        paths = self.spec["paths"]
        self.assertIn("/intelligence/analyse", paths)
        self.assertIn("/intelligence/stream", paths)
        self.assertIn("/intelligence/sessions/{stream_id}/cancel", paths)

    def test_analyse_endpoint_has_request_body(self) -> None:
        analyse = self.spec["paths"]["/intelligence/analyse"]["post"]
        self.assertIn("requestBody", analyse)
        content = analyse["requestBody"]["content"]["application/json"]["schema"]
        self.assertIn("$ref", content)
        self.assertIn("IntelligenceRequest", content["$ref"])

    def test_openapi_json_is_valid_json(self) -> None:
        raw = OpenAPIGenerator.generate_json()
        parsed = json.loads(raw)
        self.assertEqual(parsed["openapi"], "3.1.0")

    def test_sdk_models_generated(self) -> None:
        sdk = OpenAPIGenerator.generate_sdk_models()
        self.assertIn("IntelligenceRequest", sdk)
        fields = {f["name"] for f in sdk["IntelligenceRequest"]["fields"]}
        self.assertIn("workspace_id", fields)
        self.assertIn("user_id", fields)
        self.assertIn("module", fields)


# ===========================================================================
# Event publishing tests
# ===========================================================================

class TestEventPublishing(unittest.TestCase):
    """Validates that AnalysisEventPublisher emits correct events."""

    def setUp(self) -> None:
        _reset_bus()

    def test_publish_started(self) -> None:
        received: list = []

        class Recv:
            def handle(self, e):
                received.append(e)

        bus = EventBus()
        bus.subscribe(EventType.ANALYSIS_STARTED, Recv())
        pub = AnalysisEventPublisher(event_bus=bus)
        pub.publish_started(AnalysisStartedPayload(
            request_id="req-1", execution_id="exec-1",
            module="resume", workspace_id="ws-1", user_id="u-1",
        ))
        bus.dispatch_all()
        self.assertEqual(len(received), 1)

    def test_publish_completed(self) -> None:
        received: list = []

        class Recv:
            def handle(self, e):
                received.append(e)

        _reset_bus()
        bus = EventBus()
        bus.subscribe(EventType.ANALYSIS_COMPLETED, Recv())
        pub = AnalysisEventPublisher(event_bus=bus)
        pub.publish_completed(AnalysisCompletedPayload(
            request_id="req-2", execution_id="exec-2",
            module="github", status="completed",
            confidence=0.95, duration_ms=1800.0,
        ))
        bus.dispatch_all()
        self.assertEqual(len(received), 1)

    def test_publish_failed(self) -> None:
        received: list = []

        class Recv:
            def handle(self, e):
                received.append(e)

        _reset_bus()
        bus = EventBus()
        bus.subscribe(EventType.ANALYSIS_FAILED, Recv())
        pub = AnalysisEventPublisher(event_bus=bus)
        pub.publish_failed(AnalysisFailedPayload(
            request_id="req-3", execution_id="exec-3",
            module="document", error_code="provider_error", message="timeout",
        ))
        bus.dispatch_all()
        self.assertEqual(len(received), 1)
