"""Unit and integration tests validating Plugin & Extension Framework dynamic loading and cycles."""

import os
import shutil
import tempfile
import threading
import unittest
from backend.plugins.models import PluginManifest, PluginState
from backend.plugins.plugin_manager import PluginManager
from backend.plugins.dependency_resolver import DependencyResolver


class TestPluginFramework(unittest.TestCase):
    """Integration test suite validating plugin lifecycle loops, concurrency load, and sandboxes."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PluginManager(platform_version="1.0.0")
        self.ws_id = "ws-plugin-test"

        # 1. Create a mock plugin directory
        self.plugin_name = "mock_addon"
        self.plugin_dir = os.path.join(self.temp_dir, self.plugin_name)
        os.makedirs(self.plugin_dir, exist_ok=True)

        # 2. Write a mock plugin python script
        self.script_content = (
            "from backend.plugins.plugin_api import BasePlugin\n\n"
            "class MockPluginClass(BasePlugin):\n"
            "    def on_load(self) -> None:\n"
            "        self.loaded_flag = True\n"
            "    def on_enable(self) -> None:\n"
            "        self.enabled_flag = True\n"
            "    def calculate_sum(self, a, b):\n"
            "        return a + b\n"
            "    def unsafe_network_method(self):\n"
            "        return 'network_output'\n"
        )
        with open(os.path.join(self.plugin_dir, "addon.py"), "w", encoding="utf-8") as f:
            f.write(self.script_content)

        # 3. Write a mock plugin manifest.json
        self.manifest_content = (
            '{\n'
            '  "name": "mock_addon",\n'
            '  "version": "1.0.0",\n'
            '  "author": "Tester",\n'
            '  "description": "Mock plugin test description.",\n'
            '  "capabilities": ["Tool Provider"],\n'
            '  "dependencies": {},\n'
            '  "min_runtime_version": "1.0.0",\n'
            '  "permissions": [],\n'
            '  "entry_point": "addon.MockPluginClass",\n'
            '  "config_schema": {}\n'
            '}'
        )
        with open(os.path.join(self.plugin_dir, "manifest.json"), "w", encoding="utf-8") as f:
            f.write(self.manifest_content)

    def tearDown(self) -> None:
        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_plugin_discovery_and_lifecycle_transitions(self) -> None:
        """Verifies loading, enabling, executing, disabling, and status checks."""
        # Load
        self.manager.discover_and_load_plugins(self.temp_dir, self.ws_id)
        
        info = self.manager.registry.get_plugin_info(self.plugin_name)
        instance = self.manager.registry.get_plugin_instance(self.plugin_name)
        
        self.assertIsNotNone(info)
        self.assertIsNotNone(instance)
        self.assertEqual(info.state, PluginState.LOADED)
        self.assertTrue(getattr(instance, "loaded_flag", False))

        # Enable
        self.manager.enable_plugin(self.plugin_name)
        self.assertEqual(info.state, PluginState.ENABLED)
        self.assertTrue(getattr(instance, "enabled_flag", False))

        # Execute Method
        result = self.manager.execute_plugin_method(self.plugin_name, "calculate_sum", 5, 10)
        self.assertEqual(result, 15)

        # Disable
        self.manager.disable_plugin(self.plugin_name)
        self.assertEqual(info.state, PluginState.DISABLED)

    def test_sandbox_permission_block(self) -> None:
        """Verifies sandbox raises PermissionError when functions require undeclared permissions."""
        self.manager.discover_and_load_plugins(self.temp_dir, self.ws_id)
        self.manager.enable_plugin(self.plugin_name)

        # Method unsafe_network_method contains the word 'network' but permissions are empty ([])
        with self.assertRaises(Exception) as context:
            self.manager.execute_plugin_method(self.plugin_name, "unsafe_network_method")
        
        self.assertIn("requires 'network' permission", str(context.exception))

    def test_dependency_circular_detection(self) -> None:
        """Verifies topological sorting raises exceptions on circular graph flows."""
        resolver = DependencyResolver()
        
        manifest_a = PluginManifest(
            name="plugin_a", version="1.0.0", author="A", description="A",
            capabilities=["Tool"], dependencies={"plugin_b": "1.0.0"}, entry_point="entry.A"
        )
        manifest_b = PluginManifest(
            name="plugin_b", version="1.0.0", author="B", description="B",
            capabilities=["Tool"], dependencies={"plugin_a": "1.0.0"}, entry_point="entry.B"
        )
        
        manifests = {"plugin_a": manifest_a, "plugin_b": manifest_b}
        with self.assertRaises(ValueError) as context:
            resolver.resolve_load_order(manifests)
            
        self.assertIn("Circular dependency detected", str(context.exception))

    def test_concurrent_loading(self) -> None:
        """Verifies thread-safety during concurrent registration workflows."""
        import sys
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        exceptions = []

        def loader_thread(thread_idx: int):
            try:
                # Add unique items thread-safely
                manifest = PluginManifest(
                    name=f"addon_{thread_idx}", version="1.0.0", author="T", description="T",
                    capabilities=["Tool"], dependencies={}, entry_point="addon.MockPluginClass"
                )
                from backend.plugins.models import PluginInfo
                from backend.plugins.plugin_context import PluginContext
                ctx = PluginContext(manifest.name, self.ws_id)
                
                # Import dynamically loaded mock class type
                from addon import MockPluginClass
                instance = MockPluginClass(ctx)
                info = PluginInfo(manifest=manifest)
                
                self.manager.registry.register_plugin(manifest.name, info, instance)
            except Exception as e:
                exceptions.append(str(e))

        threads = [threading.Thread(target=loader_thread, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(exceptions), 0, f"Concurrency errors occurred: {exceptions}")
        registered = self.manager.registry.list_plugins()
        # Initial mock plugin + 10 thread-loaded plugins = 11
        self.assertEqual(len(registered), 10)
