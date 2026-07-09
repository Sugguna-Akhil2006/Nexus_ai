"""Comprehensive unit and E2E tests for the AI Governance & Compliance Center."""

from __future__ import annotations

import threading
import unittest

from backend.governance.models import ApprovalState, ModelRecord, RiskLevel
from backend.governance.model_registry import ModelRegistry
from backend.governance.audit_manager import AuditManager
from backend.governance.compliance_engine import ComplianceEngine
from backend.governance.approval_workflow import ApprovalWorkflow
from backend.governance.retention_manager import RetentionManager
from backend.governance.risk_assessor import RiskAssessor
from backend.governance.report_generator import ReportGenerator
from backend.governance.governance_manager import GovernanceManager


class TestModelRegistry(unittest.TestCase):
    """Verifies model registration and lifecycle updates."""

    def test_register_and_get(self) -> None:
        reg = ModelRegistry()
        model = ModelRecord(model_id="m1", name="Test Model", version="1.0", provider="ollama")
        reg.register(model)
        self.assertEqual(reg.get("m1").name, "Test Model")

    def test_update_state(self) -> None:
        reg = ModelRegistry()
        model = ModelRecord(model_id="m1", name="Test Model", version="1.0", provider="ollama")
        reg.register(model)
        reg.update_state("m1", ApprovalState.DEPRECATED)
        self.assertEqual(reg.get("m1").approval_state, ApprovalState.DEPRECATED)
        self.assertEqual(reg.get("m1").status, "deprecated")


class TestAuditManager(unittest.TestCase):
    """Verifies event audit record additions and filters."""

    def test_record_and_list(self) -> None:
        mgr = AuditManager()
        mgr.record_event("admin", "alice", "update_config")
        mgr.record_event("workflow", "bob", "run_wf")

        self.assertEqual(len(mgr.list_history()), 2)
        self.assertEqual(len(mgr.list_history("admin")), 1)


class TestComplianceEngine(unittest.TestCase):
    """Verifies compliance checks results."""

    def test_compliance_evaluation(self) -> None:
        mgr = AuditManager()
        # Non-admin log exists, but no admin logs -> admin visibility checks fail
        mgr.record_event("workflow", "bob", "run_wf")
        report = ComplianceEngine.evaluate(mgr.list_history())
        self.assertFalse(report.overall_passed)


class TestApprovalWorkflow(unittest.TestCase):
    """Verifies model workflow approval ticket transitions."""

    def test_ticket_flow(self) -> None:
        wf = ApprovalWorkflow()
        wf.submit("m1")
        self.assertEqual(wf.get_status("m1"), ApprovalState.PENDING)
        wf.approve("m1")
        self.assertEqual(wf.get_status("m1"), ApprovalState.APPROVED)


class TestRetentionManager(unittest.TestCase):
    """Verifies historical log truncation."""

    def test_retention(self) -> None:
        mgr = AuditManager()
        for i in range(10):
            mgr.record_event("workflow", "alice", f"run_{i}")

        truncated = RetentionManager.enforce_retention(mgr.list_history(), max_count=5)
        self.assertEqual(len(truncated), 5)
        self.assertEqual(truncated[-1].action, "run_9")


class TestRiskAssessor(unittest.TestCase):
    """Verifies platform risk scoring alerts."""

    def test_risk_calculation(self) -> None:
        models = [ModelRecord(model_id="m1", name="M1", version="1", provider="ollama", status="deprecated")]
        logs = []
        report = RiskAssessor.assess(models, logs)
        self.assertEqual(report.risk_level, RiskLevel.MEDIUM)
        self.assertGreater(report.score, 0.0)


class TestGovernanceManagerE2E(unittest.TestCase):
    """E2E workflow evaluations, audits, reports, and thread safety tests."""

    def setUp(self) -> None:
        self.manager = GovernanceManager()
        self.manager.cleanup()

    def test_register_and_approve(self) -> None:
        model = ModelRecord(model_id="gpt-3", name="GPT3", version="1", provider="openai")
        self.manager.register_model(model)
        self.assertEqual(self.manager.get_approval_state("gpt-3"), ApprovalState.PENDING)

        self.manager.approve_model("gpt-3")
        self.assertEqual(self.manager.get_approval_state("gpt-3"), ApprovalState.APPROVED)

    def test_generate_report_markdown(self) -> None:
        self.manager.audit_event("admin", "alice", "update_config")
        md = self.manager.generate_report("markdown")
        self.assertIn("# AI Governance Compliance & Risk Report", md)

    def test_generate_report_html(self) -> None:
        self.manager.audit_event("admin", "alice", "update_config")
        html = self.manager.generate_report("html")
        self.assertIn("<!DOCTYPE html>", html)

    def test_concurrency_audit(self) -> None:
        errors = []

        def worker(i: int) -> None:
            try:
                self.manager.audit_event("workflow", "user", f"action_{i}")
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        history = self.manager.list_audit_history()
        self.assertEqual(len(history), 50)
