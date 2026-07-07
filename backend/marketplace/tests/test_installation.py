"""Tests for package installation, updates, rollbacks, repairs, and lifecycle events."""

import unittest
from backend.marketplace.models import PackageMetadata, PackageType, MarketplacePackage
from backend.marketplace.marketplace_service import MarketplaceService
from backend.runtime.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: list[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestInstallation(unittest.TestCase):
    """Verifies that packages install, upgrade, rollback, and emit correct events."""

    def setUp(self) -> None:
        self.service = MarketplaceService(core_version="1.5.0")
        self.event_receiver = MockEventReceiver()
        self.event_bus = EventBus()
        # Reset the event bus singleton state between tests
        with self.event_bus._lock:
            self.event_bus._subscribers.clear()
            self.event_bus._queue.clear()
            self.event_bus._history.clear()
            self.event_bus._statistics = {
                "published_count": 0,
                "dispatched_count": 0,
                "failed_count": 0,
                "by_type": {}
            }
        self.event_bus.subscribe("*", self.event_receiver)

        # Register a valid package version 1.0.0 in marketplace registry
        self.meta_v1 = PackageMetadata(
            package_id="agent_pack",
            version="1.0.0",
            author="Google DeepMind",
            license="MIT",
            description="Agent suite",
            compatibility={"min_core_version": "1.0.0", "os": ["windows"]},
            digital_signature="sig:agent_pack:1.0.0:fp_deepmind_key_2026",
            checksum="3b8aa26a5d1889f170a918659081389a8193a4fe7adb84b8a7cd4a95f4be8f4c"  # SHA-256 for b"agent_pack-1.0.0-data"
        )
        self.pkg_v1 = MarketplacePackage(
            metadata=self.meta_v1,
            package_type=PackageType.PROMPT_PACK,
            publisher="Google DeepMind"
        )
        self.service.registry.register_package(self.pkg_v1)

        # Register version 2.0.0
        self.meta_v2 = PackageMetadata(
            package_id="agent_pack",
            version="2.0.0",
            author="Google DeepMind",
            license="MIT",
            description="Agent suite v2",
            compatibility={"min_core_version": "1.0.0", "os": ["windows"]},
            digital_signature="sig:agent_pack:2.0.0:fp_deepmind_key_2026",
            checksum="27a3ca36d4883447cc8990ef1b342d22f45062f080f4acbb22a16962c2e8a375"  # SHA-256 for b"agent_pack-2.0.0-data"
        )
        self.pkg_v2 = MarketplacePackage(
            metadata=self.meta_v2,
            package_type=PackageType.PROMPT_PACK,
            publisher="Google DeepMind"
        )
        self.service.registry.register_package(self.pkg_v2)

    def test_install_lifecycle(self) -> None:
        """Tests complete installation, enable, disable, and uninstall lifecycle."""
        # 1. Install package v1
        installed = self.service.install_package("agent_pack", "1.0.0")
        self.assertEqual(installed.metadata.version, "1.0.0")
        self.assertTrue(installed.enabled)

        # Assert event
        self.event_bus.dispatch_all()
        install_events = [e for e in self.event_receiver.events if e.event_type == EventType.PACKAGE_INSTALLED]
        self.assertEqual(len(install_events), 1)

        # 2. Disable package
        self.service.installer.disable("agent_pack")
        self.assertFalse(self.service.package_manager.get_installed("agent_pack").enabled)

        # 3. Enable package
        self.service.installer.enable("agent_pack")
        self.assertTrue(self.service.package_manager.get_installed("agent_pack").enabled)

        # 4. Remove package
        self.service.remove_package("agent_pack")
        self.assertIsNone(self.service.package_manager.get_installed("agent_pack"))

        self.event_bus.dispatch_all()
        remove_events = [e for e in self.event_receiver.events if e.event_type == EventType.PACKAGE_REMOVED]
        self.assertEqual(len(remove_events), 1)

    def test_update_and_rollback(self) -> None:
        """Tests updating package to v2 and rolling back to v1."""
        self.service.install_package("agent_pack", "1.0.0")

        # Update to v2
        updated = self.service.update_package("agent_pack")
        self.assertEqual(updated.metadata.version, "2.0.0")
        self.assertEqual(updated.backup_versions, ["1.0.0"])

        # Rollback back to v1
        rolled = self.service.rollback_package("agent_pack")
        self.assertEqual(rolled.metadata.version, "1.0.0")
        self.assertEqual(rolled.backup_versions, [])

    def test_compatibility_rejection(self) -> None:
        """Tests that package installation fails if framework version is too old."""
        old_core_service = MarketplaceService(core_version="0.5.0")
        old_core_service.registry.register_package(self.pkg_v1)

        with self.assertRaises(ValueError):
            old_core_service.install_package("agent_pack", "1.0.0")

    def test_repair_flow(self) -> None:
        """Tests repair reinstall logic."""
        self.service.install_package("agent_pack", "1.0.0")
        repaired = self.service.installer.repair(self.pkg_v1, b"agent_pack-1.0.0-data")
        self.assertEqual(repaired.metadata.version, "1.0.0")
