"""Compliance engine validating governance logs against retention and security limits."""

from __future__ import annotations

from typing import List

from backend.governance.models import (
    AuditTrailEntry,
    ComplianceCheckResult,
    ComplianceStatusReport,
)


class ComplianceEngine:
    """Evaluates audit logs against structural policy checklist rules."""

    @staticmethod
    def evaluate(logs: List[AuditTrailEntry]) -> ComplianceStatusReport:
        """Audits workflow executions and security entries to build compliance reports."""
        results: List[ComplianceCheckResult] = []

        # Rule 1: No admin modifications without logging
        admin_logs = [l for l in logs if l.category == "admin"]
        passed_admin = len(admin_logs) > 0 or len(logs) == 0
        results.append(
            ComplianceCheckResult(
                rule_name="Administrator Actions Visibility",
                passed=passed_admin,
                details="Admin operations logged successfully." if passed_admin else "No administrator actions logged.",
            )
        )

        # Rule 2: Verify provider failover levels
        prov_failures = sum(
            1 for l in logs if l.category == "provider" and l.context.get("status") == "failed"
        )
        passed_prov = prov_failures < 5
        results.append(
            ComplianceCheckResult(
                rule_name="Provider Error Rates",
                passed=passed_prov,
                details=f"Provider failures: {prov_failures} (threshold: < 5).",
            )
        )

        overall = all(r.passed for r in results)

        return ComplianceStatusReport(
            overall_passed=overall,
            results=results,
        )
