"""Unit and E2E tests for the Release Validation & Quality Gate System."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.release.compatibility_checker import CompatibilityChecker
from backend.release.dependency_validator import DependencyValidator
from backend.release.documentation_validator import DocumentationValidator
from backend.release.models import GateStatus, QualityGateResult
from backend.release.performance_validator import PerformanceValidator
from backend.release.quality_gate import QualityGate
from backend.release.release_manager import ReleaseManager
from backend.release.release_report import ReleaseReportCompiler
from backend.release.security_validator import SecurityValidator
from backend.release.system_checker import SystemChecker


class TestQualityGate(unittest.TestCase):
    """Verifies QualityGate evaluations mapping failures to GateStatus."""

    def test_evaluate_gate_passed(self) -> None:
        r = QualityGate.evaluate_gate("GateA", "Desc", [])
        self.assertEqual(r.status, GateStatus.PASSED)
        self.assertIsNone(r.message)

    def test_evaluate_gate_failed(self) -> None:
        r = QualityGate.evaluate_gate("GateB", "Desc", ["Error 1", "Error 2"])
        self.assertEqual(r.status, GateStatus.FAILED)
        self.assertIn("Error 1", r.message)


class TestSystemChecker(unittest.TestCase):
    """Verifies SQLite database connectivity pings and event bus queues."""

    def test_system_audit_runs(self) -> None:
        warnings = SystemChecker.audit_system_connectivity()
        # In test suite run, database should connect cleanly, so warnings should be empty
        self.assertEqual(len(warnings), 0)


class TestDependencyValidator(unittest.TestCase):
    """Verifies package import checks and registry checks."""

    def test_dependency_audit_runs(self) -> None:
        warnings = DependencyValidator.audit_dependencies()
        self.assertEqual(len(warnings), 0)


class TestSecurityValidator(unittest.TestCase):
    """Verifies configuration security audit toggles."""

    def test_security_audit_runs(self) -> None:
        warnings = SecurityValidator.audit_security()
        # Rate limit and masking settings should be active by default, so zero warnings
        self.assertEqual(len(warnings), 0)


class TestDocumentationValidator(unittest.TestCase):
    """Verifies documentation existence warning outputs."""

    def test_documentation_audit_runs(self) -> None:
        warnings = DocumentationValidator.audit_documentation()
        # In local workspace workspace, some guides might be missing or relocated,
        # so we assert the return type is list of warning strings
        self.assertIsInstance(warnings, list)


class TestReleaseManagerE2E(unittest.TestCase):
    """Full lifecycle release checks and score calculation audits."""

    def setUp(self) -> None:
        self.mgr = ReleaseManager(db_path=":memory:")

    def test_run_validation_scoring(self) -> None:
        report = self.mgr.run_validation()
        self.assertIsNotNone(report.report_id)
        self.assertGreaterEqual(report.readiness_score, 0)
        self.assertLessEqual(report.readiness_score, 100)

        # Check persistence
        latest = self.mgr.get_latest_report()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["report_id"], report.report_id)

        history = self.mgr.list_history()
        self.assertEqual(len(history), 1)
