"""Compliance checker supporting GDPR, SOC2, and ISO 27001 rules validation."""

from __future__ import annotations

from typing import Any, Dict

from backend.governance.models import ComplianceStatus, SecurityCheckResult


class ComplianceChecker:
    """Validates alignment with industry compliance standards (GDPR, SOC2, ISO 27001)."""

    def check_compliance(self, context: Dict[str, Any], security_result: SecurityCheckResult) -> ComplianceStatus:
        """Evaluates framework rules and returns unified compliance status record.

        Args:
            context: Context details.
            security_result: Results from safety checks.

        Returns:
            ComplianceStatus: Compliance status summary.
        """
        reasons = []
        gdpr = True
        soc2 = True
        iso = True
        enterprise = True

        # 1. GDPR: Fail if PII data leaks are found
        if security_result.detected_pii:
            gdpr = False
            reasons.append("GDPR: Unencrypted PII detected in execution payload.")

        # 2. SOC2: Fail if auditing parameters or workspace IDs are missing
        if not context.get("workspace_id") or not context.get("user_id"):
            soc2 = False
            reasons.append("SOC2: Missing workspace isolation or audit identity context.")

        # 3. ISO 27001: Fail if prompt injection risk is critical/unresolved
        if security_result.has_prompt_injection:
            iso = False
            reasons.append("ISO 27001: Critical prompt injection risk detected, exposing infrastructure.")

        # 4. Enterprise Compliance checks
        cost = context.get("cost", 0.0)
        if cost > 5.0:  # Custom enterprise cost threshold limit
            enterprise = False
            reasons.append(f"Enterprise Policy: Cost ${cost:.2f} exceeds standard budget constraints.")

        return ComplianceStatus(
            gdpr_compliant=gdpr,
            soc2_compliant=soc2,
            iso_compliant=iso,
            enterprise_compliant=enterprise,
            non_compliant_reasons=reasons
        )
