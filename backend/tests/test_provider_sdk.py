import concurrent.futures
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.sdk.provider_sdk import (
    ProviderSDKError,
    ProviderValidationError,
    ProviderConnectionError,
    ProviderCapabilities,
    RetryPolicy,
    ProviderConfiguration,
    ProviderMetrics,
    BaseProvider,
    ProviderRegistry,
    ErrorMapper,
    MockDatabaseProvider,
)
from backend.runtime.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestProviderSDK(unittest.TestCase):
    """Suite of tests covering the Provider SDK plugin foundation."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = ProviderRegistry()
        with self.registry._lock:
            self.registry._providers.clear()

        self.retry_policy = RetryPolicy(mode="exponential", max_attempts=4)
        self.config = ProviderConfiguration(
            provider_id="mock_db",
            name="Mock Database",
            version="1.0.0",
            endpoint="localhost:5432",
            credentials={"password": "secret_password123"},
            retry_policy=self.retry_policy
        )
        self.provider = MockDatabaseProvider(config=self.config)

    def test_credentials_masking(self) -> None:
        """Verifies configuration __repr__ obfuscates credentials keys secrets."""
        representation = repr(self.config)
        self.assertNotIn("secret_password123", representation)
        self.assertIn("********", representation)

    def test_metrics_tracking(self) -> None:
        """Verifies latency averages, token counters, and success rate tracking."""
        metrics = ProviderMetrics()
        metrics.record(success=True, latency=0.1, tokens=50)
        metrics.record(success=True, latency=0.2, tokens=30)
        metrics.record(success=False, latency=0.3, tokens=0)

        data = metrics.metrics
        self.assertEqual(data["requests"], 3)
        self.assertEqual(data["failures"], 1)
        self.assertEqual(data["token_usage"], 80)
        self.assertAlmostEqual(data["success_rate"], 2.0 / 3.0)
        self.assertAlmostEqual(data["average_latency"], 0.2)
        self.assertGreater(data["uptime"], 0.0)

    def test_registry_lifecycle_and_events(self) -> None:
        """Verifies registers, starts, health checks, stops, and event dispatches."""
        self.registry.register_provider(self.provider)
        self.assertIn(self.provider, self.registry.list_providers())

        # Duplicate register
        with self.assertRaises(ProviderValidationError):
            self.registry.register_provider(self.provider)

        # Start
        self.provider.initialize()
        self.provider.start()

        # Health
        health = self.registry.health_check()
        self.assertTrue(health["mock_db"])

        # Supports Capabilities
        self.assertTrue(self.provider.supports("embeddings"))
        self.assertFalse(self.provider.supports("chat"))

        # Stop
        self.provider.stop()

        # Unregister
        self.registry.unregister_provider("mock_db")
        self.assertNotIn("mock_db", [p.config.provider_id for p in self.registry.list_providers()])

        # Verify EventBus notifications
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("provider.registered", events)
        self.assertIn("provider.started", events)
        self.assertIn("provider.health.checked", events)
        self.assertIn("provider.stopped", events)

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of ProviderRegistry."""
        registry2 = ProviderRegistry()
        self.assertIs(self.registry, registry2)

    def test_error_mapper(self) -> None:
        """Verifies standard exception translation mappings."""
        raw_exc = ValueError("mismatch parameters")
        mapped = ErrorMapper.map_exception(raw_exc)
        self.assertIsInstance(mapped, ProviderSDKError)

        # Base exceptions bypass mapper
        sdk_exc = ProviderValidationError("validation failed")
        mapped_sdk = ErrorMapper.map_exception(sdk_exc)
        self.assertIs(mapped_sdk, sdk_exc)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations operate safely."""
        def run_thread(tid: int) -> None:
            class TempProvider(BaseProvider):
                @property
                def capabilities(self): return ProviderCapabilities()
                def initialize(self): pass
                def health_check(self): return True

            cfg = ProviderConfiguration(
                provider_id=f"temp-{tid}",
                name="Temp",
                version="1.0.0",
                endpoint="local"
            )
            prov = TempProvider(config=cfg)
            self.registry.register_provider(prov)
            self.assertIs(self.registry.get_provider(f"temp-{tid}"), prov)
            self.registry.unregister_provider(f"temp-{tid}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
