import concurrent.futures
from datetime import datetime
import threading
from typing import Any, Dict, List, Optional
import unittest
import uuid

from core.sdk import (
    SDKError,
    SDKValidationError,
    SDKCompatibilityError,
    ExtensionType,
    SDKVersion,
    SDKManifest,
    SDKBase,
    CompatibilityValidator,
    SDKRegistry,
    SDKUtilities,
    DefaultSDKScaffolder,
    MockAgentExtension,
)
from core.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestSDKSystem(unittest.TestCase):
    """Suite of tests covering semantic version validators, registries, and scaffolders."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = SDKRegistry()
        with self.registry._lock:
            self.registry._extensions.clear()

        self.mock_ext = MockAgentExtension()

    def test_version_and_compatibility_validator(self) -> None:
        """Verifies CompatibilityValidator validates or rejects major semver matrices."""
        # 1. Compatible manifest
        manifest_ok = SDKManifest(
            extension_name="test_ext",
            extension_type=ExtensionType.TOOL,
            sdk_version="1.0.0",
            runtime_version="1.5.0",
            author="Developer",
            license="MIT",
            capabilities=[]
        )
        CompatibilityValidator.validate_compatibility(manifest_ok)

        # 2. Incompatible SDK version (major mismatch 2.0.0 vs 1.0.0)
        manifest_bad_sdk = SDKManifest(
            extension_name="test_ext",
            extension_type=ExtensionType.TOOL,
            sdk_version="2.0.0",
            runtime_version="1.0.0",
            author="Developer",
            license="MIT",
            capabilities=[]
        )
        with self.assertRaises(SDKCompatibilityError):
            CompatibilityValidator.validate_compatibility(manifest_bad_sdk)

        # 3. Incompatible Runtime version (major mismatch 0.0.1 vs 1.0.0)
        manifest_bad_rt = SDKManifest(
            extension_name="test_ext",
            extension_type=ExtensionType.TOOL,
            sdk_version="1.0.0",
            runtime_version="0.0.1",
            author="Developer",
            license="MIT",
            capabilities=[]
        )
        with self.assertRaises(SDKCompatibilityError):
            CompatibilityValidator.validate_compatibility(manifest_bad_rt)

        # 4. Invalid SemVer format
        manifest_invalid_format = SDKManifest(
            extension_name="test_ext",
            extension_type=ExtensionType.TOOL,
            sdk_version="1.0",  # missing patch
            runtime_version="1.0.0",
            author="Developer",
            license="MIT",
            capabilities=[]
        )
        with self.assertRaises(SDKValidationError):
            CompatibilityValidator.validate_compatibility(manifest_invalid_format)

    def test_scaffolder(self) -> None:
        """Verifies default scaffolder creates JSON templates and starting classes."""
        scaffolder = DefaultSDKScaffolder()
        files = scaffolder.scaffold("/target", "MyAgent", ExtensionType.AGENT)

        self.assertIn("manifest.json", files)
        self.assertIn("extension.py", files)
        self.assertIn("MyAgent", files["manifest.json"])
        self.assertIn("AGENT", files["manifest.json"])
        self.assertIn("class MyAgentExtension(SDKBase):", files["extension.py"])

        with self.assertRaises(SDKValidationError):
            scaffolder.scaffold("/target", "", ExtensionType.AGENT)

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of SDKRegistry."""
        registry2 = SDKRegistry()
        self.assertIs(self.registry, registry2)

    def test_registry_registration_and_lifecycle(self) -> None:
        """Verifies extension registration, validation, health, and removal transitions."""
        # Setup mock extension state
        self.mock_ext.initialize()
        self.mock_ext.start()
        self.assertTrue(self.mock_ext.initialized)
        self.assertTrue(self.mock_ext.running)

        # Register
        self.registry.register(self.mock_ext)
        self.assertIn(self.mock_ext, self.registry.discover())

        # Validate
        valid = self.registry.validate("mock_agent_ext")
        self.assertTrue(valid)
        self.assertTrue(self.mock_ext.validated)

        # Health
        health = self.registry.health_check()
        self.assertTrue(health["mock_agent_ext"])

        # Unregister
        self.registry.unregister("mock_agent_ext")
        self.assertFalse(self.mock_ext.running)
        self.assertNotIn(self.mock_ext, self.registry.discover())

        # Verify EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("sdk.extension.registered", events)
        self.assertIn("sdk.extension.loaded", events)
        self.assertIn("sdk.extension.validated", events)
        self.assertIn("sdk.extension.removed", events)

    def test_registry_validation_errors(self) -> None:
        """Verifies validation parameter rejections for register tasks."""
        with self.assertRaises(SDKValidationError):
            self.registry.register(None)  # type: ignore

        # Duplicate register
        self.registry.register(self.mock_ext)
        with self.assertRaises(SDKValidationError):
            self.registry.register(self.mock_ext)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            class DummyExtension(SDKBase):
                @property
                def manifest(self):
                    return SDKManifest(
                        extension_name=f"dummy-{tid}",
                        extension_type=ExtensionType.CUSTOM,
                        sdk_version="1.0.0",
                        runtime_version="1.0.0",
                        author="Dev",
                        license="MIT",
                        capabilities=[]
                    )
                def initialize(self): pass
                def validate(self): pass
                def start(self): pass
                def stop(self): pass
                def shutdown(self): pass
                def health_check(self): return True

            ext = DummyExtension()
            self.registry.register(ext)
            self.assertIn(ext, self.registry.discover())
            self.registry.unregister(f"dummy-{tid}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
