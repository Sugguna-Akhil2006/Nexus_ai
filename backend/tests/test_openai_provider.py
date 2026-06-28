import time
from typing import Any, Dict, List, Optional
import unittest
import urllib.error
import uuid

from backend.providers.openai_provider import (
    RetryPolicy,
    ProviderConfiguration,
    ProviderMetrics,
    ErrorMapper,
    StreamingAdapter,
    OpenAIProvider,
)
from backend.runtime.event import Event, EventBus, EventType
from backend.interfaces.model import (
    InferenceRequest,
    EmbeddingRequest,
    ModelValidationError,
    ModelNotFoundError,
    ModelCapability,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestOpenAIProvider(unittest.TestCase):
    """Suite of tests covering the OpenAI Provider Plugin."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.config = ProviderConfiguration(
            api_key="mock-key-12345678",
            base_url="mock://api.openai.com/v1"
        )
        self.provider = OpenAIProvider(config=self.config)

    def test_configuration_masking(self) -> None:
        """Verifies api_key secrets are obfuscated in config __repr__."""
        representation = repr(self.config)
        self.assertNotIn("12345678", representation)
        self.assertIn("mock...", representation)

    def test_metrics_collection(self) -> None:
        """Verifies thread-safe provider metrics recording."""
        metrics = ProviderMetrics()
        metrics.record(tokens=100, latency=0.15, success=True, rate_limit=950)
        metrics.record(tokens=0, latency=0.05, success=False, rate_limit=900)

        data = metrics.metrics
        self.assertEqual(data["requests"], 2)
        self.assertEqual(data["tokens"], 100)
        self.assertEqual(data["errors"], 1)
        self.assertEqual(data["rate_limit_remaining"], 900)

    def test_error_mapping(self) -> None:
        """Verifies HTTP status codes translate to correct ModelErrors."""
        # 1. 404 Not Found
        exc_404 = urllib.error.HTTPError("http://api/chat", 404, "Not Found", {}, None)  # type: ignore
        mapped_404 = ErrorMapper.map_exception(exc_404, "gpt-4o")
        self.assertIsInstance(mapped_404, ModelNotFoundError)

        # 2. 400 Bad Request
        exc_400 = urllib.error.HTTPError("http://api/chat", 400, "Bad Request", {}, None)  # type: ignore
        mapped_400 = ErrorMapper.map_exception(exc_400, "gpt-4o")
        self.assertIsInstance(mapped_400, ModelValidationError)

        # 3. 401 Unauthorized
        exc_401 = urllib.error.HTTPError("http://api/chat", 401, "Unauthorized", {}, None)  # type: ignore
        mapped_401 = ErrorMapper.map_exception(exc_401, "gpt-4o")
        self.assertIsInstance(mapped_401, ModelValidationError)

    def test_sse_line_parsing(self) -> None:
        """Verifies SSE line parsing extraction of JSON strings."""
        line = 'data: {"id": "chatcmpl-123", "choices": [{"delta": {"content": "hello"}}]}'
        parsed = StreamingAdapter.parse_sse_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["id"], "chatcmpl-123")  # type: ignore

        # DONE tag returns None
        done = "data: [DONE]"
        self.assertIsNone(StreamingAdapter.parse_sse_line(done))

    def test_provider_generate(self) -> None:
        """Verifies generate creates choices and triggers events."""
        req = InferenceRequest(model="gpt-4o", prompt="hello AI")
        res = self.provider.generate(req)

        self.assertEqual(res.provider, "openai")
        self.assertEqual(res.model, "gpt-4o")
        self.assertIn("Mock OpenAI response", res.content)

        # Check EventBus
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.request.started", events)
        self.assertIn("provider.request.completed", events)

    def test_provider_generate_stream(self) -> None:
        """Verifies streaming yield chunks iterations."""
        req = InferenceRequest(model="gpt-4o", prompt="hello AI stream")
        chunks = list(self.provider.generate_stream(req))

        self.assertGreater(len(chunks), 1)
        self.assertTrue(any("streaming" in c.content for c in chunks))

        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.stream.started", events)

    def test_provider_embed(self) -> None:
        """Verifies embed generates dimensions vectors."""
        req = EmbeddingRequest(model="text-embedding-3-small", input="hello vector")
        res = self.provider.embed(req)

        self.assertEqual(len(res.embeddings), 1)
        self.assertEqual(len(res.embeddings[0]), 1536)

    def test_provider_metadata_discovery(self) -> None:
        """Verifies list_models capabilities lists."""
        models = self.provider.list_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0].model_id, "gpt-4o")

        # Supports
        self.assertTrue(self.provider.supports(ModelCapability.CHAT))
        self.assertTrue(self.provider.supports(ModelCapability.EMBEDDING))

        # Get Model
        info = self.provider.get_model("gpt-4o")
        self.assertEqual(info.context_window, 128000)

        with self.assertRaises(ModelNotFoundError):
            self.provider.get_model("non-existent")

    def test_simulated_error_raising(self) -> None:
        """Verifies error conditions raise ValidationError."""
        req = InferenceRequest(
            model="gpt-4o",
            prompt="hello",
            metadata={"trigger_error": True}
        )
        with self.assertRaises(ModelValidationError):
            self.provider.generate(req)
