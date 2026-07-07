"""Unit and integration tests for the Workflow Templates & Automation Library."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.workflow_library.automation_scheduler import AutomationScheduler
from backend.workflow_library.models import TemplateScope, WorkflowTemplate
from backend.workflow_library.recommendation_engine import RecommendationEngine
from backend.workflow_library.template_executor import TemplateExecutor
from backend.workflow_library.template_import_export import TemplateImportExport
from backend.workflow_library.template_manager import TemplateManager
from backend.workflow_library.template_permissions import TemplatePermissions
from backend.workflow_library.template_registry import TemplateRegistry
from backend.workflow_library.template_versioning import TemplateVersioning


class TestTemplateRegistry(unittest.TestCase):
    """Verifies SQLite registry CRUD operations and builtin seeds."""

    def setUp(self) -> None:
        self.registry = TemplateRegistry(db_path=":memory:")

    def test_crud_and_seed(self) -> None:
        # Check seeded builtins
        templates = self.registry.list_templates()
        self.assertGreater(len(templates), 0)
        self.assertTrue(any(t.template_id == "tpl-resume-review" for t in templates))

        # Add custom
        tpl = WorkflowTemplate(
            template_id="custom-1",
            name="Custom Template",
            steps=["Step A"],
            scope=TemplateScope.PRIVATE,
            created_at="2026",
        )
        self.registry.save_template(tpl)
        retrieved = self.registry.get_template("custom-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Custom Template")

        # Delete
        self.registry.delete_template("custom-1")
        self.assertIsNone(self.registry.get_template("custom-1"))


class TestTemplateVersioning(unittest.TestCase):
    """Verifies version snapshots compiling."""

    def setUp(self) -> None:
        self.versioning = TemplateVersioning(db_path=":memory:")

    def test_snapshots(self) -> None:
        tpl = WorkflowTemplate(
            template_id="tpl-1",
            name="Template 1",
            steps=["Step A"],
            version="1.0.0",
            created_at="2026",
        )
        self.versioning.save_version_snapshot(tpl, "Initial Version")
        versions = self.versioning.list_versions("tpl-1")
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0].version, "1.0.0")


class TestTemplateExecutorAndScheduler(unittest.TestCase):
    """Verifies manual runs outcomes and cron schedules registers."""

    def setUp(self) -> None:
        self.scheduler = AutomationScheduler(db_path=":memory:")

    def test_executor(self) -> None:
        tpl = WorkflowTemplate(
            template_id="tpl-1",
            name="Template 1",
            steps=["Step A"],
            created_at="2026",
        )
        log = TemplateExecutor.execute(tpl)
        self.assertEqual(log.status, "success")
        self.assertEqual(log.template_id, "tpl-1")

    def test_scheduler(self) -> None:
        sched = self.scheduler.schedule_template("tpl-1", "0 9 * * 1-5")
        self.assertEqual(sched.cron_expression, "0 9 * * 1-5")
        self.assertTrue(sched.enabled)


class TestTemplatePermissions(unittest.TestCase):
    """Verifies template accessibility scopes."""

    def test_sharing_access(self) -> None:
        tpl_marketplace = WorkflowTemplate(
            template_id="t1",
            name="Public",
            scope=TemplateScope.MARKETPLACE,
            created_at="2026",
        )
        tpl_private = WorkflowTemplate(
            template_id="t2",
            name="Private",
            scope=TemplateScope.PRIVATE,
            author="author-1",
            created_at="2026",
        )

        self.assertTrue(TemplatePermissions.can_access(tpl_marketplace, "user-1", "ws-1"))
        self.assertTrue(TemplatePermissions.can_access(tpl_private, "author-1", "ws-1"))
        self.assertFalse(TemplatePermissions.can_access(tpl_private, "user-2", "ws-1"))


class TestTemplateImportExport(unittest.TestCase):
    """Verifies JSON models serialization loops."""

    def test_export_import(self) -> None:
        tpl = WorkflowTemplate(
            template_id="tpl-123",
            name="Template Test",
            steps=["Step A"],
            created_at="2026",
        )
        json_str = TemplateImportExport.export_to_json(tpl)
        imported = TemplateImportExport.import_from_json(json_str)
        self.assertIsNotNone(imported)
        self.assertEqual(imported.name, "Template Test")


class TestRecommendationEngine(unittest.TestCase):
    """Verifies workspace trait suggestion queries."""

    def test_recommendations(self) -> None:
        # Request with resume traits
        suggestions = RecommendationEngine.suggest_templates("resume profiling", ["my_resume.pdf"])
        self.assertTrue(any(t.template_id == "tpl-resume-review" for t in suggestions))

        # Request with code traits
        suggestions_code = RecommendationEngine.suggest_templates("repository auditing", ["main.go"])
        self.assertTrue(any(t.template_id == "tpl-github-review" for t in suggestions_code))
