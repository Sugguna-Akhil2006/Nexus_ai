import time
from typing import Any, Dict, List, Optional
import unittest
import urllib.error
import uuid

from backend.providers.ollama_provider import (
    OllamaConfiguration,
    OllamaProvider,
    ErrorMapper,
)
from backend.runtime.event import Event, EventBus, EventType
from backend.interfaces.model import (
    InferenceRequest,
    EmbeddingRequest,
    ModelValidationError,
    ModelNotFoundError,
    ModelCapability,
    ModelError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestOllamaProvider(unittest.TestCase):
    """Suite of tests covering the local Ollama Provider Plugin."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.config = OllamaConfiguration(
            host="mock-host",
            port=11434,
            metadata={"mock": True}
        )
        self.provider = OllamaProvider(config=self.config)
        self.provider.initialize()

    def test_configuration_defaults(self) -> None:
        """Verifies default OllamaConfiguration parameters."""
        cfg = OllamaConfiguration()
        self.assertEqual(cfg.host, "localhost")
        self.assertEqual(cfg.port, 11434)
        self.assertEqual(cfg.timeout, 30.0)

    def test_error_mapping(self) -> None:
        """Verifies connection and HTTP errors map to correct ModelErrors."""
        # 1. 404 Not Found
        exc_404 = urllib.error.HTTPError("http://api/chat", 404, "Not Found", {}, None)  # type: ignore
        mapped_404 = ErrorMapper.map_exception(exc_404, "llama3")
        self.assertIsInstance(mapped_404, ModelNotFoundError)

        # 2. 400 Bad Request
        exc_400 = urllib.error.HTTPError("http://api/chat", 400, "Bad Request", {}, None)  # type: ignore
        mapped_400 = ErrorMapper.map_exception(exc_400, "llama3")
        self.assertIsInstance(mapped_400, ModelValidationError)

        # 3. Connection URLError
        exc_conn = urllib.error.URLError("refused connection")
        mapped_conn = ErrorMapper.map_exception(exc_conn, "llama3")
        self.assertIsInstance(mapped_conn, ModelError)

    def test_provider_generate(self) -> None:
        """Verifies generate completes and updates metrics log tracks."""
        req = InferenceRequest(model="llama3", prompt="why is the sky blue?")
        res = self.provider.generate(req)

        self.assertEqual(res.provider, "ollama")
        self.assertEqual(res.model, "llama3")
        self.assertIn("Mock local Ollama response", res.content)

        metrics = self.provider.metrics.metrics
        self.assertEqual(metrics["requests"], 1)
        self.assertEqual(metrics["failures"], 0)

        # EventBus events
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.request.started", events)
        self.assertIn("provider.request.completed", events)

    def test_provider_generate_stream(self) -> None:
        """Verifies generate_stream yields word chunks."""
        req = InferenceRequest(model="llama3", prompt="why is the sky blue?")
        chunks = list(self.provider.generate_stream(req))

        self.assertEqual(len(chunks), 4)
        self.assertEqual(chunks[3].finish_reason, "stop")

        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.stream.started", events)

    def test_provider_embed(self) -> None:
        """Verifies embed generates 768 dimensions list vector."""
        req = EmbeddingRequest(model="nomic-embed-text", input="hello vector")
        res = self.provider.embed(req)

        self.assertEqual(len(res.embeddings), 1)
        self.assertEqual(len(res.embeddings[0]), 768)

    def test_local_model_management(self) -> None:
        """Verifies pull and delete model management updates."""
        # Pull model
        self.provider.pull_model("llama3")
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.model.pulled", events)

        # Delete model
        self.provider.delete_model("llama3")

    def test_model_discovery(self) -> None:
        """Verifies discovery tags lists cached models metadata."""
        models = self.provider.list_models()
        self.assertEqual(len(models), 2)
        self.assertEqual(models[0].model_id, "llama3")

        # Get Model
        info = self.provider.get_model("llama3")
        self.assertEqual(info.context_window, 8192)

        # Health checked
        self.assertTrue(self.provider.health_check())

        # Supports
        self.assertTrue(self.provider.supports(ModelCapability.CHAT))
        self.assertTrue(self.provider.supports(ModelCapability.EMBEDDING))
