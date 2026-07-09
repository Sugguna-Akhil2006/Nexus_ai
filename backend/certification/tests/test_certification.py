"""Certification suite tests: unit, failure simulation, and regression."""

from __future__ import annotations

import unittest

from backend.certification.models import (
    CertificationDomain,
    CertificationLevel,
    CheckResult,
    CheckStatus,
    DomainReport,
)
from backend.certification.report_generator import ReportGenerator
from backend.certification.scorecard import Scorecard
from backend.certification.runtime_certifier import RuntimeCertifier
from backend.certification.security_certifier import SecurityCertifier
from backend.certification.workflow_certifier import WorkflowCertifier
from backend.certification.knowledge_certifier import KnowledgeCertifier
from backend.certification.performance_certifier import PerformanceCertifier
from backend.certification.integration_certifier import IntegrationCertifier
from backend.certification.certification_manager import CertificationManager


def _domain_with_checks(*statuses: CheckStatus, domain: CertificationDomain = CertificationDomain.RUNTIME) -> DomainReport:
    """Helper to build a DomainReport with the given check statuses."""
    report = DomainReport(domain=domain)
    for i, status in enumerate(statuses):
        report.checks.append(
            CheckResult(
                name=f"Check_{i}",
                domain=domain,
                status=status,
                critical=(status == CheckStatus.FAILED and i == 0),
            )
        )
    return report


class TestScorecard(unittest.TestCase):
    """Verifies scoring arithmetic and level assignment."""

    def test_perfect_score(self) -> None:
        report = _domain_with_checks(CheckStatus.PASSED, CheckStatus.PASSED)
        score = Scorecard.compute_domain_score(report)
        self.assertEqual(score, 100)

    def test_failure_deduction(self) -> None:
        # One regular failure = -5
        report = _domain_with_checks(CheckStatus.PASSED, CheckStatus.FAILED)
        # Check 1 is not critical (i=1), so -5
        report.checks[1].critical = False
        score = Scorecard.compute_domain_score(report)
        self.assertEqual(score, 95)

    def test_critical_failure_deduction(self) -> None:
        # One critical failure = -20
        report = _domain_with_checks(CheckStatus.FAILED)
        report.checks[0].critical = True
        score = Scorecard.compute_domain_score(report)
        self.assertEqual(score, 80)

    def test_warning_deduction(self) -> None:
        report = _domain_with_checks(CheckStatus.WARNING)
        score = Scorecard.compute_domain_score(report)
        self.assertEqual(score, 99)

    def test_score_floors_at_zero(self) -> None:
        # 10 critical failures should not go below 0
        report = _domain_with_checks(*[CheckStatus.FAILED] * 10)
        for c in report.checks:
            c.critical = True
        score = Scorecard.compute_domain_score(report)
        self.assertEqual(score, 0)

    def test_level_enterprise(self) -> None:
        self.assertEqual(Scorecard.award_level(100), CertificationLevel.ENTERPRISE)
        self.assertEqual(Scorecard.award_level(95), CertificationLevel.ENTERPRISE)

    def test_level_gold(self) -> None:
        self.assertEqual(Scorecard.award_level(85), CertificationLevel.GOLD)
        self.assertEqual(Scorecard.award_level(90), CertificationLevel.GOLD)

    def test_level_silver(self) -> None:
        self.assertEqual(Scorecard.award_level(70), CertificationLevel.SILVER)

    def test_level_bronze(self) -> None:
        self.assertEqual(Scorecard.award_level(50), CertificationLevel.BRONZE)

    def test_level_none(self) -> None:
        self.assertEqual(Scorecard.award_level(30), CertificationLevel.NONE)


class TestRuntimeCertifier(unittest.TestCase):
    """Verifies runtime certifier produces a domain report."""

    def test_certify_returns_report(self) -> None:
        report = RuntimeCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.RUNTIME)
        self.assertGreater(len(report.checks), 0)


class TestSecurityCertifier(unittest.TestCase):
    """Verifies security certifier produces expected checks."""

    def test_certify_returns_report(self) -> None:
        report = SecurityCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.SECURITY)
        check_names = [c.name for c in report.checks]
        self.assertIn("Input Validation", check_names)


class TestWorkflowCertifier(unittest.TestCase):
    """Verifies workflow certifier."""

    def test_certify_returns_report(self) -> None:
        report = WorkflowCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.WORKFLOW)
        self.assertGreater(len(report.checks), 0)


class TestKnowledgeCertifier(unittest.TestCase):
    """Verifies knowledge certifier."""

    def test_certify_returns_report(self) -> None:
        report = KnowledgeCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.KNOWLEDGE)
        self.assertGreater(len(report.checks), 0)


class TestPerformanceCertifier(unittest.TestCase):
    """Verifies performance certifier."""

    def test_certify_returns_report(self) -> None:
        report = PerformanceCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.PERFORMANCE)
        self.assertGreater(len(report.checks), 0)


class TestIntegrationCertifier(unittest.TestCase):
    """Verifies integration certifier."""

    def test_certify_returns_report(self) -> None:
        report = IntegrationCertifier.certify()
        self.assertEqual(report.domain, CertificationDomain.INTEGRATION)
        self.assertGreater(len(report.checks), 0)


class TestCertificationManagerE2E(unittest.TestCase):
    """End-to-end certification run with scoring and level assignment."""

    def test_full_run(self) -> None:
        manager = CertificationManager()
        run = manager.run()
        self.assertIsNotNone(run.run_id)
        self.assertGreater(run.total_checks, 0)
        self.assertGreaterEqual(run.overall_score, 0)
        self.assertLessEqual(run.overall_score, 100)
        self.assertIn(
            run.certification_level.value,
            ["bronze", "silver", "gold", "enterprise", "none"],
        )

    def test_history_recorded(self) -> None:
        manager = CertificationManager()
        manager.run()
        history = manager.get_history()
        self.assertGreater(len(history), 0)


class TestReportGenerator(unittest.TestCase):
    """Verifies report output formats."""

    def _make_run(self) -> object:
        manager = CertificationManager()
        return manager.run()

    def test_markdown_report_contains_score(self) -> None:
        run = self._make_run()
        md = ReportGenerator.to_markdown(run)
        self.assertIn("Overall Score", md)
        self.assertIn(str(run.overall_score), md)

    def test_json_report_parseable(self) -> None:
        import json
        run = self._make_run()
        raw = ReportGenerator.to_json(run)
        data = json.loads(raw)
        self.assertIn("run_id", data)

    def test_html_report_structure(self) -> None:
        run = self._make_run()
        html = ReportGenerator.to_html(run)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(run.run_id, html)
