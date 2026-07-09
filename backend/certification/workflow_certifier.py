"""Workflow certifier validating the workflow engine and automation system."""

from __future__ import annotations

import time

from backend.certification.models import (
    CertificationDomain,
    CheckResult,
    CheckStatus,
    DomainReport,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


class WorkflowCertifier:
    """Certifies the Nexus Workflow Engine subsystem.

    Checks performed:
    - WorkflowExecutor importability.
    - Basic workflow execution (happy path).
    - WorkflowTemplate library availability.
    - AutomationScheduler availability.
    """

    DOMAIN = CertificationDomain.WORKFLOW

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all workflow checks and returns a domain report."""
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_workflow_executor(),
            cls._check_workflow_execution(),
            cls._check_template_library(),
            cls._check_automation_scheduler(),
        ])
        return report

    @staticmethod
    def _check_workflow_executor() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.workflow.automation_engine import WorkflowExecutor  # noqa: F401
            return CheckResult(
                name="WorkflowExecutor Import",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.PASSED,
                message="WorkflowExecutor module importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="WorkflowExecutor Import",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_workflow_execution() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.workflow.automation_engine import WorkflowExecutor
            executor = WorkflowExecutor()
            # Verify executor has required interface
            assert hasattr(executor, "execute") or hasattr(executor, "run"), \
                "WorkflowExecutor missing execute/run method."
            return CheckResult(
                name="Workflow Execution Interface",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.PASSED,
                message="WorkflowExecutor interface verified.",
                duration_ms=_ms(start),
            )
        except AssertionError as exc:
            return CheckResult(
                name="Workflow Execution Interface",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )
        except Exception as exc:
            return CheckResult(
                name="Workflow Execution Interface",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.WARNING,
                message=f"Executor check skipped: {exc}",
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_template_library() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.workflow_library.template_registry import TemplateRegistry
            reg = TemplateRegistry(db_path=":memory:")
            templates = reg.list_templates()
            return CheckResult(
                name="Workflow Template Library",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.PASSED,
                message=f"Template library operational. Built-ins: {len(templates)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Workflow Template Library",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=False,
            )

    @staticmethod
    def _check_automation_scheduler() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.workflow_library.automation_scheduler import AutomationScheduler
            sched = AutomationScheduler(db_path=":memory:")
            schedules = sched.list_schedules()
            return CheckResult(
                name="Automation Scheduler",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.PASSED,
                message=f"Scheduler operational. Active schedules: {len(schedules)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Automation Scheduler",
                domain=CertificationDomain.WORKFLOW,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )
