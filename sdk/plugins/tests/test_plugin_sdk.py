"""Comprehensive tests for the Plugin SDK & Extension API."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from sdk.plugins.examples.weather_connector import WeatherConnector
from sdk.plugins.models import (
    PluginPermission,
    PluginStatus,
    PluginType,
)
from sdk.plugins.plugin_builder import PluginBuilder
from sdk.plugins.plugin_events import PluginEvents
from sdk.plugins.plugin_lifecycle import PluginLifecycle
from sdk.plugins.plugin_manifest import PluginManifest
from sdk.plugins.plugin_packager import PluginPackager
from sdk.plugins.plugin_permissions import PluginPermissions
from sdk.plugins.plugin_testing import PluginTesting
from sdk.plugins.plugin_validator import PluginValidator


def _make_manifest(
    plugin_id: str = "sample_plugin",
    name: str = "Sample Plugin",
    entry_point: str = "sdk.plugins.examples.weather_connector:WeatherConnector",
) -> object:
    """Helper to build a valid test manifest."""
    return (
        PluginManifest()
        .id(plugin_id)
        .name(name)
        .version("1.0.0")
        .author("Test Author")
        .description("A test plugin.")
        .plugin_type(PluginType.CONNECTOR)
        .permission(PluginPermission.NETWORK)
        .compatible_with(">=1.0.0")
        .entry_point(entry_point)
        .build()
    )


class TestPluginManifest(unittest.TestCase):
    """Verifies fluent PluginManifest builder output."""

    def test_build_valid(self) -> None:
        manifest = _make_manifest()
        self.assertEqual(manifest.plugin_id, "sample_plugin")
        self.assertEqual(manifest.version, "1.0.0")
        self.assertIn(PluginPermission.NETWORK, manifest.permissions)

    def test_build_missing_id_raises(self) -> None:
        with self.assertRaises(ValueError):
            PluginManifest().name("No ID Plugin").entry_point("a.b:C").build()

    def test_build_missing_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            PluginManifest().id("no_name").entry_point("a.b:C").build()


class TestPluginValidator(unittest.TestCase):
    """Verifies validation rules for manifests."""

    def test_valid_manifest_passes(self) -> None:
        result = PluginValidator.validate(_make_manifest())
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_invalid_plugin_id_fails(self) -> None:
        manifest = _make_manifest()
        manifest.plugin_id = "Invalid ID!"
        result = PluginValidator.validate(manifest)
        self.assertFalse(result.valid)
        self.assertTrue(any("snake_case" in e for e in result.errors))

    def test_bad_semver_fails(self) -> None:
        manifest = _make_manifest()
        manifest.version = "not-a-version"
        result = PluginValidator.validate(manifest)
        self.assertFalse(result.valid)


class TestPluginLifecycle(unittest.TestCase):
    """Verifies install/enable/disable/update/reload/remove operations."""

    def setUp(self) -> None:
        self.lifecycle = PluginLifecycle()
        self.manifest = _make_manifest()

    def test_install_and_list(self) -> None:
        record = self.lifecycle.install(self.manifest)
        self.assertEqual(record.status, PluginStatus.INSTALLED)
        self.assertEqual(len(self.lifecycle.list_plugins()), 1)

    def test_enable_disable_cycle(self) -> None:
        self.lifecycle.install(self.manifest)
        record = self.lifecycle.enable("sample_plugin")
        self.assertEqual(record.status, PluginStatus.ENABLED)
        record = self.lifecycle.disable("sample_plugin")
        self.assertEqual(record.status, PluginStatus.DISABLED)

    def test_update_bumps_version(self) -> None:
        self.lifecycle.install(self.manifest)
        record = self.lifecycle.update("sample_plugin", "2.0.0")
        self.assertEqual(record.manifest.version, "2.0.0")

    def test_reload(self) -> None:
        self.lifecycle.install(self.manifest)
        self.lifecycle.enable("sample_plugin")
        record = self.lifecycle.reload("sample_plugin")
        self.assertEqual(record.status, PluginStatus.ENABLED)

    def test_remove(self) -> None:
        self.lifecycle.install(self.manifest)
        self.lifecycle.remove("sample_plugin")
        self.assertIsNone(self.lifecycle.get("sample_plugin"))

    def test_duplicate_install_raises(self) -> None:
        self.lifecycle.install(self.manifest)
        with self.assertRaises(ValueError):
            self.lifecycle.install(self.manifest)

    def test_events_recorded(self) -> None:
        self.lifecycle.install(self.manifest)
        self.lifecycle.enable("sample_plugin")
        event_types = [e.event_type.value for e in self.lifecycle.events()]
        self.assertIn("plugin.loaded", event_types)
        self.assertIn("plugin.enabled", event_types)


class TestPluginPermissions(unittest.TestCase):
    """Verifies permission scope enforcement."""

    def test_has_permission(self) -> None:
        manifest = _make_manifest()
        self.assertTrue(PluginPermissions.has_permission(manifest, PluginPermission.NETWORK))
        self.assertFalse(PluginPermissions.has_permission(manifest, PluginPermission.FILESYSTEM))

    def test_high_risk_warning(self) -> None:
        manifest = _make_manifest()
        warnings = PluginPermissions.evaluate(manifest)
        self.assertTrue(any("high-risk" in w for w in warnings))

    def test_assert_permission_raises(self) -> None:
        manifest = _make_manifest()
        with self.assertRaises(PermissionError):
            PluginPermissions.assert_permission(manifest, PluginPermission.FILESYSTEM)


class TestPluginEvents(unittest.TestCase):
    """Verifies the plugin event bus dispatch."""

    def test_subscribe_and_emit(self) -> None:
        from sdk.plugins.models import PluginEvent, PluginEventType
        bus = PluginEvents()
        received = []

        bus.subscribe(PluginEventType.ENABLED, lambda e: received.append(e.plugin_id))
        bus.emit(PluginEvent(event_type=PluginEventType.ENABLED, plugin_id="test_plugin"))

        self.assertEqual(received, ["test_plugin"])

    def test_decorator_registration(self) -> None:
        from sdk.plugins.models import PluginEvent, PluginEventType
        bus = PluginEvents()
        calls = []

        @bus.on(PluginEventType.REMOVED)
        def handle(event: PluginEvent) -> None:
            calls.append(event.plugin_id)

        bus.emit(PluginEvent(event_type=PluginEventType.REMOVED, plugin_id="removed_plugin"))
        self.assertEqual(calls, ["removed_plugin"])


class TestPluginBuilder(unittest.TestCase):
    """Verifies plugin project file generation."""

    def test_generates_expected_files(self) -> None:
        manifest = _make_manifest("my_connector", "My Connector")
        files = PluginBuilder.generate_files(manifest)
        self.assertIn("my_connector/__init__.py", files)
        self.assertIn("my_connector/plugin.py", files)
        self.assertIn("my_connector/tests/test_my_connector.py", files)
        # plugin.py must contain the class name
        self.assertIn("class MyConnector", files["my_connector/plugin.py"])


class TestPluginPackager(unittest.TestCase):
    """Verifies ZIP packaging and inspection."""

    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp(dir=os.path.dirname(__file__))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_package_and_inspect(self) -> None:
        manifest = _make_manifest()
        files = {"sample_plugin/__init__.py": '"""Package."""\n'}
        archive = PluginPackager.package(manifest, files, self.tmp_dir)
        self.assertTrue(os.path.exists(archive))
        info = PluginPackager.inspect(archive)
        self.assertEqual(info["manifest"]["plugin_id"], "sample_plugin")
        self.assertIn("CHECKSUMS.sha256", info["files"])


class TestPluginTesting(unittest.TestCase):
    """Verifies the lifecycle test harness."""

    def test_lifecycle_passes_for_example(self) -> None:
        manifest = WeatherConnector().manifest
        result = PluginTesting.run_lifecycle_tests(manifest, WeatherConnector)
        self.assertTrue(result.success)
        self.assertEqual(result.failed, 0)
