"""Unit and E2E integration tests for the Internal Developer Platform."""

from __future__ import annotations

import os
import shutil
import unittest
from datetime import datetime

from backend.idp.code_quality import CodeQualityAuditor
from backend.idp.dependency_analyzer import DependencyAnalyzer
from backend.idp.developer_cli import DeveloperCLI
from backend.idp.documentation_generator import DocumentationGenerator
from backend.idp.lint_manager import LintManager
from backend.idp.migration_generator import MigrationGenerator
from backend.idp.models import ScaffoldRequest, ScaffoldType
from backend.idp.module_generator import ModuleGenerator
from backend.idp.project_scaffolder import ProjectScaffolder


class TestProjectScaffolder(unittest.TestCase):
    """Verifies boilerplate scaffolding generation and directory setups."""

    def setUp(self) -> None:
        self.base_temp = os.path.abspath(os.path.join(os.path.dirname(__file__), ".temp_scaffold"))
        os.makedirs(self.base_temp, exist_ok=True)

    def tearDown(self) -> None:
        if os.path.exists(self.base_temp):
            shutil.rmtree(self.base_temp)

    def test_scaffolding(self) -> None:
        req = ScaffoldRequest(
            scaffold_type=ScaffoldType.MODULE,
            name="test_mod",
            description="A test module component.",
        )
        res = ProjectScaffolder.scaffold(req, self.base_temp)
        self.assertTrue(res.success)
        self.assertGreater(len(res.generated_files), 0)

        # Check files existence
        target_path = os.path.join(self.base_temp, "generated", "test_mod")
        self.assertTrue(os.path.exists(os.path.join(target_path, "__init__.py")))
        self.assertTrue(os.path.exists(os.path.join(target_path, "models.py")))


class TestModuleAndMigrationGenerators(unittest.TestCase):
    """Verifies routing, service, and SQL upgrade script builders."""

    def test_code_generators(self) -> None:
        api_code = ModuleGenerator.generate_api_router_code("TestComponent")
        self.assertIn("class ActionPayload(BaseModel):", api_code)

        srv_code = ModuleGenerator.generate_service_code("TestComponent")
        self.assertIn("class TestComponentService:", srv_code)

    def test_migration_generator(self) -> None:
        migration = MigrationGenerator.generate_migration("add_user_roles", "ALTER TABLE users ADD COLUMN role TEXT;")
        self.assertEqual(len(migration), 1)
        filename = list(migration.keys())[0]
        self.assertTrue(filename.endswith(".sql"))
        self.assertIn("ALTER TABLE users ADD COLUMN role TEXT;", migration[filename])


class TestDependencyAnalyzer(unittest.TestCase):
    """Verifies circular dependency audits."""

    def test_circular_imports_detection(self) -> None:
        files = {
            "auth.py": "import db\nimport session",
            "db.py": "import auth\nimport connection",
        }
        circulars = DependencyAnalyzer.detect_circular_dependencies(files)
        self.assertEqual(len(circulars), 1)
        self.assertIn("Circular import detected: auth <--> db", circulars[0])


class TestCodeQualityAndLinter(unittest.TestCase):
    """Verifies PEP8 standards and lints checks."""

    def test_line_lengths(self) -> None:
        long_line = "a" * 150
        warnings = CodeQualityAuditor.audit_quality(long_line)
        self.assertEqual(len(warnings), 1)
        self.assertIn("exceeds maximum line length", warnings[0])

    def test_raw_prints(self) -> None:
        code = "def test():\n    print('debugging')\n"
        warnings = LintManager.lint_code(code)
        self.assertEqual(len(warnings), 1)
        self.assertIn("raw print statement used", warnings[0])


class TestDeveloperCLI(unittest.TestCase):
    """Verifies terminal command simulations."""

    def test_doctor_command(self) -> None:
        res = DeveloperCLI.process_command(["nexus", "doctor"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("healthy", res.output)

    def test_validate_command(self) -> None:
        res = DeveloperCLI.process_command(["nexus", "validate"])
        self.assertEqual(res.exit_code, 0)
        self.assertIn("PEP8 Check", res.output)

    def test_invalid_command(self) -> None:
        res = DeveloperCLI.process_command(["nexus", "invalid"])
        self.assertEqual(res.exit_code, 1)
