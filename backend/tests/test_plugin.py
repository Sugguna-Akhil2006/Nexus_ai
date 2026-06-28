import json
import os
import shutil
import tempfile
import threading
from typing import Any, Dict, List
import unittest

from backend.runtime.event import Event, EventBus, EventType
from backend.interfaces.plugin import (
    DefaultPluginInstance,
    Plugin,
    PluginBase,
    PluginCapability,
    PluginDependencyError,
    PluginError,
    PluginManager,
    PluginNotFoundError,
    PluginState,
    PluginValidationError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class DummyPlugin(PluginBase):
    """Custom plugin base for tracking hooks execution."""

    def __init__(self) -> None:
        self.initialized = False
        self.started = False
        self.stopped = False
        self.shutdown_done = False
        self.config = {}

    def initialize(self) -> None:
        self.initialized = True

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def shutdown(self) -> None:
        self.shutdown_done = True

    def configuration_schema(self) -> Dict[str, Any]:
        return {"param": "string"}


class FailingPlugin(PluginBase):
    """Custom plugin designed to crash on start."""

    def start(self) -> None:
        raise RuntimeError("Crash on start")


class TestPluginSystem(unittest.TestCase):
    """Suite of tests covering the Runtime Plugin System."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(plugins_dir=self.temp_dir)
        with self.manager._lock:
            self.manager._plugins.clear()
            self.manager._instances.clear()
            self.manager._states.clear()
            self.manager.set_plugins_dir(self.temp_dir)
        self.event_bus = EventBus()
        self.event_bus.clear()

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir)

    def test_singleton(self) -> None:
        """Verifies that PluginManager behaves as a singleton."""
        manager2 = PluginManager()
        self.assertIs(self.manager, manager2)

    def test_manual_registration_validation(self) -> None:
        """Verifies validations enforce ID uniqueness and runtime version checks."""
        # Incompatible runtime version
        p_incompat = Plugin(
            plugin_id="p1",
            name="Incompat",
            version="1.0.0",
            author="Author",
            description="",
            license="",
            runtime_version=">=2.0.0"
        )
        with self.assertRaises(PluginValidationError):
            self.manager.register(p_incompat)

        # Empty/whitespace ID
        p_empty = Plugin(
            plugin_id="",
            name="Empty",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*"
        )
        with self.assertRaises(PluginValidationError):
            self.manager.register(p_empty)

        # Duplicate ID
        p_ok = Plugin(
            plugin_id="p_ok",
            name="OK",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*"
        )
        self.manager.register(p_ok)
        with self.assertRaises(PluginValidationError):
            self.manager.register(p_ok)

    def test_dependency_resolution(self) -> None:
        """Verifies dependency ordering resolution and cycle detections."""
        p1 = Plugin(
            plugin_id="A",
            name="A",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*",
            dependencies=["B", "C"]
        )
        p2 = Plugin(
            plugin_id="B",
            name="B",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*",
            dependencies=["C"]
        )
        p3 = Plugin(
            plugin_id="C",
            name="C",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*"
        )

        self.manager.register(p1)
        self.manager.register(p2)
        self.manager.register(p3)

        # Deterministic ordering: C has 0 deps, B depends on C, A depends on B & C
        # Load order should be: C, B, A
        order = self.manager.resolve_dependencies()
        self.assertEqual(order, ["C", "B", "A"])

    def test_dependency_missing_raises(self) -> None:
        """Verifies missing dependencies raise PluginDependencyError."""
        p1 = Plugin(
            plugin_id="A",
            name="A",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*",
            dependencies=["MissingDep"]
        )
        self.manager.register(p1)
        with self.assertRaises(PluginDependencyError):
            self.manager.resolve_dependencies()

    def test_dependency_circular_raises(self) -> None:
        """Verifies circular dependency loops raise PluginDependencyError."""
        p1 = Plugin(
            plugin_id="A",
            name="A",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*",
            dependencies=["B"]
        )
        p2 = Plugin(
            plugin_id="B",
            name="B",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*",
            dependencies=["A"]
        )
        self.manager.register(p1)
        self.manager.register(p2)
        with self.assertRaises(PluginDependencyError):
            self.manager.resolve_dependencies()

    def test_lifecycle_states_and_hooks(self) -> None:
        """Verifies plugin state transitions and lifecycle callbacks execution."""
        plugin = Plugin(
            plugin_id="test_lifecycle",
            name="Test Lifecycle Plugin",
            version="1.0.0",
            author="Test",
            description="",
            license="",
            runtime_version="*",
            capabilities=[PluginCapability.CUSTOM]
        )
        instance = DummyPlugin()

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # 1. Register (Discovered)
        self.manager.register(plugin, instance)
        self.assertEqual(self.manager._states["test_lifecycle"], PluginState.DISCOVERED)

        # 2. Load
        self.manager.load("test_lifecycle")
        self.assertEqual(self.manager._states["test_lifecycle"], PluginState.LOADED)
        self.assertTrue(instance.initialized)

        # 3. Enable
        self.manager.enable("test_lifecycle")
        self.assertEqual(self.manager._states["test_lifecycle"], PluginState.ENABLED)
        self.assertTrue(instance.started)
        self.assertIn(PluginCapability.CUSTOM, self.manager.list_capabilities())

        # 4. Disable
        self.manager.disable("test_lifecycle")
        self.assertEqual(self.manager._states["test_lifecycle"], PluginState.DISABLED)
        self.assertTrue(instance.stopped)

        # 5. Unload
        self.manager.unload("test_lifecycle")
        self.assertEqual(self.manager._states["test_lifecycle"], PluginState.UNLOADED)
        self.assertTrue(instance.shutdown_done)

        # Check Event Bus
        self.event_bus.dispatch_all()
        event_names = [e.payload["event_name"] for e in receiver.events]
        self.assertIn("plugin.discovered", event_names)
        self.assertIn("plugin.loaded", event_names)
        self.assertIn("plugin.enabled", event_names)
        self.assertIn("plugin.disabled", event_names)
        self.assertIn("plugin.unloaded", event_names)

    def test_failing_plugin_transitions_to_failed(self) -> None:
        """Verifies hook failure transitions plugin to FAILED state."""
        plugin = Plugin(
            plugin_id="fail_plug",
            name="Failer",
            version="1.0.0",
            author="",
            description="",
            license="",
            runtime_version="*"
        )
        instance = FailingPlugin()
        self.manager.register(plugin, instance)

        with self.assertRaises(PluginError):
            self.manager.enable("fail_plug")

        self.assertEqual(self.manager._states["fail_plug"], PluginState.FAILED)

    def test_manifest_discovery(self) -> None:
        """Verifies disk scanning discover manifest registration."""
        # Create folder structure
        plug_path = os.path.join(self.temp_dir, "my_plugin")
        os.makedirs(plug_path, exist_ok=True)

        manifest_data = {
            "plugin_id": "com.test.myplugin",
            "name": "Disk Plugin",
            "version": "1.2.3",
            "author": "Disk Author",
            "runtime_version": ">=1.0.0",
            "capabilities": ["STORAGE_PROVIDER"]
        }

        with open(os.path.join(plug_path, "manifest.json"), "w") as f:
            json.dump(manifest_data, f)

        # Trigger discover
        discovered = self.manager.discover()
        self.assertEqual(len(discovered), 1)
        self.assertEqual(discovered[0].plugin_id, "com.test.myplugin")
        self.assertEqual(discovered[0].version, "1.2.3")
        self.assertIn(PluginCapability.STORAGE_PROVIDER, discovered[0].capabilities)

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent registrations under multithreading loads."""
        num_threads = 15
        registrations_per_thread = 20

        def worker(thread_idx: int) -> None:
            for i in range(registrations_per_thread):
                plugin = Plugin(
                    plugin_id=f"Thread_{thread_idx}_Plug_{i}",
                    name="Concur",
                    version="1.0.0",
                    author="",
                    description="",
                    license="",
                    runtime_version="*"
                )
                self.manager.register(plugin)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(
            len(self.manager.list_plugins()),
            num_threads * registrations_per_thread
        )


if __name__ == "__main__":
    unittest.main()
