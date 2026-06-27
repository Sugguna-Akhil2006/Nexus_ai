from dataclasses import replace
import threading
from typing import Any, Dict, Iterator, List
import unittest
import uuid

from core.event import Event, EventBus, EventType
from core.model import (
    EmbeddingRequest,
    EmbeddingResponse,
    InferenceRequest,
    InferenceResponse,
    ModelCapability,
    ModelInfo,
    ModelNotFoundError,
    ModelProvider,
    ModelRegistry,
    ModelValidationError,
    ProviderNotFoundError,
    UnsupportedCapabilityError,
    ModelError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class DummyModelProvider(ModelProvider):
    """Custom provider adapter for test mock executions."""

    def __init__(self, provider_id: str, models: List[ModelInfo]) -> None:
        self._provider_id = provider_id
        self._models = models
        self.generated_requests: List[InferenceRequest] = []
        self.embedded_requests: List[EmbeddingRequest] = []

    def generate(self, request: InferenceRequest) -> InferenceResponse:
        self.generated_requests.append(request)
        return InferenceResponse(
            request_id=str(uuid.uuid4()),
            content=f"Mock response for: {request.prompt or request.messages[-1]['content']}",
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
            latency=0.1,
            provider=self._provider_id,
            model=request.model
        )

    def generate_stream(self, request: InferenceRequest) -> Iterator[InferenceResponse]:
        yield self.generate(request)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.embedded_requests.append(request)
        # return mock vector coordinates matching input lengths
        embeddings = [[0.1, 0.2, 0.3]]
        if isinstance(request.input, list):
            embeddings = [[0.1 * i, 0.2, 0.3] for i in range(len(request.input))]

        return EmbeddingResponse(
            request_id=str(uuid.uuid4()),
            embeddings=embeddings,
            token_usage={"prompt_tokens": 5, "total_tokens": 5},
            latency=0.05,
            provider=self._provider_id,
            model=request.model
        )

    def list_models(self) -> List[ModelInfo]:
        return self._models

    def get_model(self, model_id: str) -> ModelInfo:
        for m in self._models:
            if m.model_id == model_id:
                return m
        raise ModelNotFoundError(f"Model '{model_id}' not found.")

    def health_check(self) -> bool:
        return True

    def supports(self, capability: ModelCapability) -> bool:
        for m in self._models:
            if capability in m.capabilities:
                return True
        return False


class TestModelSystem(unittest.TestCase):
    """Suite of tests covering the Model Abstraction and Registry system."""

    def setUp(self) -> None:
        self.registry = ModelRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()

        # Build mock models info
        self.chat_model_info = ModelInfo(
            model_id="nexus-chat-v1",
            provider="dummy-prov",
            name="Nexus Chat V1",
            version="1.0.0",
            context_window=4096,
            max_output_tokens=2048,
            supported_modalities=["text"],
            capabilities=[ModelCapability.CHAT, ModelCapability.STREAMING]
        )

        self.embed_model_info = ModelInfo(
            model_id="nexus-embed-v1",
            provider="dummy-prov",
            name="Nexus Embed V1",
            version="1.0.0",
            context_window=2048,
            max_output_tokens=0,
            supported_modalities=["text"],
            capabilities=[ModelCapability.EMBEDDING]
        )

        self.provider = DummyModelProvider(
            provider_id="dummy-prov",
            models=[self.chat_model_info, self.embed_model_info]
        )

    def test_singleton(self) -> None:
        """Verifies that ModelRegistry behaves as a singleton."""
        registry2 = ModelRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration_validation(self) -> None:
        """Verifies registrations enforce uniqueness constraints and validate fields."""
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Successful registration
        self.registry.register_provider("dummy-prov", self.provider)
        self.assertIn("dummy-prov", self.registry.list_providers())

        # Duplicate provider ID raises ModelValidationError
        with self.assertRaises(ModelValidationError):
            self.registry.register_provider("dummy-prov", self.provider)

        # Duplicate model ID across different providers raises ModelValidationError
        dup_chat_model = ModelInfo(
            model_id="nexus-chat-v1",  # Duplicate ID
            provider="another-prov",
            name="Another Chat V1",
            version="1.0.0",
            context_window=2048,
            max_output_tokens=1024,
            supported_modalities=["text"],
            capabilities=[ModelCapability.CHAT]
        )
        another_provider = DummyModelProvider(
            provider_id="another-prov",
            models=[dup_chat_model]
        )
        with self.assertRaises(ModelValidationError):
            self.registry.register_provider("another-prov", another_provider)

        # Check Event Bus registered event
        self.event_bus.dispatch_all()
        registered_events = [e for e in receiver.events if e.payload["event_name"] == "model.provider.registered"]
        self.assertEqual(len(registered_events), 1)

    def test_unregister_provider(self) -> None:
        """Verifies provider removal from active registries."""
        self.registry.register_provider("dummy-prov", self.provider)
        self.assertIn("dummy-prov", self.registry.list_providers())

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        self.registry.unregister_provider("dummy-prov")
        self.assertNotIn("dummy-prov", self.registry.list_providers())

        with self.assertRaises(ProviderNotFoundError):
            self.registry.get_provider("dummy-prov")

        self.event_bus.dispatch_all()
        removed_events = [e for e in receiver.events if e.payload["event_name"] == "model.provider.removed"]
        self.assertEqual(len(removed_events), 1)

    def test_model_resolution_and_matching(self) -> None:
        """Verifies retrieving model metadata catalogs and query matching properties."""
        self.registry.register_provider("dummy-prov", self.provider)

        # Retrieve direct model info
        info = self.registry.get_model("nexus-chat-v1")
        self.assertEqual(info.name, "Nexus Chat V1")

        # Missing model ID lookup raises ModelNotFoundError
        with self.assertRaises(ModelNotFoundError):
            self.registry.get_model("non-existent-model")

        # Capability matching check
        embed_models = self.registry.find_by_capability(ModelCapability.EMBEDDING)
        self.assertEqual(len(embed_models), 1)
        self.assertEqual(embed_models[0].model_id, "nexus-embed-v1")

    def test_inference_routing_and_validation(self) -> None:
        """Verifies generate request routing, validation checks, and exceptions mapping."""
        self.registry.register_provider("dummy-prov", self.provider)

        # Validate capabilities check - chat request fails if model only supports embedding
        req_chat_bad = InferenceRequest(
            model="nexus-embed-v1",
            messages=[{"role": "user", "content": "hello"}]
        )
        with self.assertRaises(UnsupportedCapabilityError):
            self.registry.generate(req_chat_bad)

        # Successful routing
        req_ok = InferenceRequest(
            model="nexus-chat-v1",
            messages=[{"role": "user", "content": "say hello"}]
        )
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        res = self.registry.generate(req_ok)
        self.assertEqual(res.content, "Mock response for: say hello")
        self.assertEqual(res.provider, "dummy-prov")

        # Event checks
        self.event_bus.dispatch_all()
        start_events = [e for e in receiver.events if e.payload["event_name"] == "model.request.started"]
        completed_events = [e for e in receiver.events if e.payload["event_name"] == "model.request.completed"]
        self.assertEqual(len(start_events), 1)
        self.assertEqual(len(completed_events), 1)

    def test_embedding_routing_and_validation(self) -> None:
        """Verifies vector embedding generation routing."""
        self.registry.register_provider("dummy-prov", self.provider)

        req_embed = EmbeddingRequest(
            model="nexus-embed-v1",
            input=["word1", "word2"]
        )
        res = self.registry.embed(req_embed)
        self.assertEqual(len(res.embeddings), 2)
        self.assertEqual(res.embeddings[0], [0.0, 0.2, 0.3])  # derived by index: 0.1 * 0 = 0.0

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent registrations under multi-threaded load conditions."""
        num_threads = 10
        registrations_per_thread = 15

        def worker(thread_idx: int) -> None:
            models = [
                ModelInfo(
                    model_id=f"t_{thread_idx}_model_{i}",
                    provider=f"t_{thread_idx}_prov",
                    name="ConcurModel",
                    version="1.0.0",
                    context_window=2048,
                    max_output_tokens=1024,
                    supported_modalities=["text"],
                    capabilities=[ModelCapability.CHAT]
                )
                for i in range(registrations_per_thread)
            ]
            prov = DummyModelProvider(
                provider_id=f"t_{thread_idx}_prov",
                models=models
            )
            self.registry.register_provider(f"t_{thread_idx}_prov", prov)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(
            len(self.registry.list_providers()),
            num_threads
        )
        self.assertEqual(
            len(self.registry.list_models()),
            num_threads * registrations_per_thread
        )


if __name__ == "__main__":
    unittest.main()
