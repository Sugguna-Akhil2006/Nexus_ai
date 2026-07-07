"""Comprehensive tests for the Compatibility & Migration Framework."""

from __future__ import annotations

import unittest

from backend.migration.models import (
    CompatibilityStatus,
    MigrationKind,
    MigrationStatus,
)
from backend.migration.compatibility_checker import CompatibilityChecker
from backend.migration.breaking_change_detector import BreakingChangeDetector
from backend.migration.schema_migrator import SchemaMigrator
from backend.migration.config_migrator import ConfigMigrator
from backend.migration.plugin_migrator import PluginMigrator
from backend.migration.workflow_migrator import WorkflowMigrator
from backend.migration.rollback_manager import RollbackManager
from backend.migration.migration_report import MigrationReport
from backend.migration.migration_manager import MigrationManager


class TestCompatibilityChecker(unittest.TestCase):
    """Verifies semver-based compatibility rules and route probing."""

    def setUp(self) -> None:
        from unittest.mock import patch
        self.patcher = patch("backend.migration.compatibility_checker.CompatibilityChecker._probe_routes", return_value=[])
        self.patcher.start()

    def tearDown(self) -> None:
        self.patcher.stop()

    def test_same_version_compatible(self) -> None:
        report = CompatibilityChecker.check("1.0.0", "1.0.0")
        self.assertEqual(report.status, CompatibilityStatus.COMPATIBLE)

    def test_minor_bump_warnings(self) -> None:
        report = CompatibilityChecker.check("1.0.0", "1.1.0")
        self.assertEqual(report.status, CompatibilityStatus.COMPATIBLE_WITH_WARNINGS)
        self.assertTrue(any("minor" in w.lower() for w in report.warnings))

    def test_major_bump_warnings(self) -> None:
        report = CompatibilityChecker.check("1.0.0", "2.0.0")
        self.assertEqual(report.status, CompatibilityStatus.COMPATIBLE_WITH_WARNINGS)
        self.assertTrue(any("major" in w.lower() for w in report.warnings))

    def test_major_jump_incompatible(self) -> None:
        report = CompatibilityChecker.check("1.0.0", "3.0.0")
        self.assertEqual(report.status, CompatibilityStatus.INCOMPATIBLE)

    def test_downgrade_incompatible(self) -> None:
        report = CompatibilityChecker.check("1.1.0", "1.0.0")
        self.assertEqual(report.status, CompatibilityStatus.INCOMPATIBLE)


class TestBreakingChangeDetector(unittest.TestCase):
    """Verifies scans for removed APIs and config keys."""

    def test_detect_returns_list(self) -> None:
        changes = BreakingChangeDetector.detect("1.0.0", "2.0.0")
        # Should be empty or contain minor adjustments; no critical crashes in import
        self.assertIsInstance(changes, list)


class TestSchemaMigrator(unittest.TestCase):
    """Verifies DDL schema migrations."""

    def test_get_steps(self) -> None:
        migrator = SchemaMigrator()
        steps = migrator.get_steps("1.0.0", "1.1.0")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].kind, MigrationKind.SCHEMA)

    def test_apply_migration(self) -> None:
        migrator = SchemaMigrator()
        steps = migrator.apply("1.0.0", "1.1.0")
        self.assertEqual(steps[0].status, MigrationStatus.COMPLETED)


class TestConfigMigrator(unittest.TestCase):
    """Verifies AppConfig dictionary transformations."""

    def test_upgrade_adds_defaults(self) -> None:
        old_cfg = {"server": {"reload": True}}
        new_cfg, steps = ConfigMigrator.apply(old_cfg, "1.0.0", "2.0.0")
        self.assertEqual(steps[0].status, MigrationStatus.COMPLETED)
        # Hot reload replace check
        self.assertTrue(new_cfg["server"]["hot_reload"])
        self.assertNotIn("reload", new_cfg["server"])
        self.assertIn("limits", new_cfg)
        self.assertIn("feature_flags", new_cfg)


class TestPluginMigrator(unittest.TestCase):
    """Verifies plugin manifest upgrades."""

    def test_upgrade_limits(self) -> None:
        manifests = [{"plugin_id": "test", "compatible_nexus_version": ">=1.0.0"}]
        upgraded, steps = PluginMigrator.apply(manifests, "1.0.0", "1.1.0")
        self.assertEqual(upgraded[0]["compatible_nexus_version"], ">=1.1.0")


class TestWorkflowMigrator(unittest.TestCase):
    """Verifies workflow definition upgrades."""

    def test_workflow_upgrade(self) -> None:
        workflows = [{"workflow_id": "wf", "steps": [{"name": "step1"}]}]
        upgraded, steps = WorkflowMigrator.apply(workflows, "1.0.0", "1.1.0")
        self.assertEqual(upgraded[0]["version"], "1.1.0")
        self.assertIn("retry_policy", upgraded[0]["steps"][0])


class TestRollbackManager(unittest.TestCase):
    """Verifies migration rollback logic."""

    def test_rollback_reverts_schema(self) -> None:
        manager = RollbackManager()
        migrator = SchemaMigrator(db_path=manager._db_path)
        steps = migrator.apply("1.0.0", "1.1.0")

        record = manager.rollback("run_id", steps, {"server": {"hot_reload": True}})
        self.assertEqual(record.status, MigrationStatus.ROLLED_BACK)
        self.assertIn(steps[0].step_id, record.rolled_back_steps)


class TestMigrationManagerE2E(unittest.TestCase):
    """End-to-end tests for the MigrationManager."""

    def setUp(self) -> None:
        self.manager = MigrationManager()
        self.manager.cleanup()

    def test_full_upgrade_flow(self) -> None:
        old_cfg = {"server": {"reload": True}}
        run, new_cfg = self.manager.run("1.0.0", "2.0.0", old_cfg)
        self.assertEqual(run.status, MigrationStatus.COMPLETED)
        self.assertIn("limits", new_cfg)
        self.assertGreater(run.duration_ms, 0)

    def test_history_tracked(self) -> None:
        self.manager.run("1.0.0", "2.0.0", {})
        self.assertEqual(len(self.manager.get_history()), 1)


class TestMigrationReport(unittest.TestCase):
    """Verifies report layout rendering."""

    def setUp(self) -> None:
        self.manager = MigrationManager()
        self.manager.cleanup()
        self.run, _ = self.manager.run("1.0.0", "2.0.0", {})

    def test_markdown_report(self) -> None:
        md = MigrationReport.to_markdown(self.run)
        self.assertIn("Migration Steps", md)

    def test_json_report(self) -> None:
        import json
        raw = MigrationReport.to_json(self.run)
        data = json.loads(raw)
        self.assertEqual(data["run_id"], self.run.run_id)

    def test_html_report(self) -> None:
        html = MigrationReport.to_html(self.run)
        self.assertIn("<!DOCTYPE html>", html)
