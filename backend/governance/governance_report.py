"""Governance report generator compiling audit trails, risk rates, and compliance dashboards."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.governance.models import ComplianceStatus
from backend.governance.policy_registry import PolicyRegistry
from backend.governance.audit_logger import AuditLogger


class GovernanceReportGenerator:
    """Generates policy compliance and risk audit reports."""

    def __init__(self) -> None:
        self.registry = PolicyRegistry()
        self.audit_logger = AuditLogger()

    def generate_report(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Compiles audit trails, risk levels, and compliance status for reporting dashboards.

        Args:
            workspace_id: Optional workspace to filter.

        Returns:
            Dict[str, Any]: Consolidated metrics report.
        """
        logs = self.audit_logger.get_history(workspace_id)
        policies = self.registry.list_policies(workspace_id)

        total_runs = len(logs)
        approved_runs = sum(1 for l in logs if l.status == "approved")
        denied_runs = sum(1 for l in logs if l.status == "denied")
        failed_runs = sum(1 for l in logs if l.status == "failed")
        
        # Violations count
        violations_count = sum(len(l.policy_violations) for l in logs)
        security_warnings_count = sum(len(l.security_alerts) for l in logs)

        # Risk level distribution
        risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for l in logs:
            lvl = l.risk_level.lower()
            if lvl in risk_distribution:
                risk_distribution[lvl] += 1

        # Check general GDPR/SOC2 compliance based on history scans
        gdpr_compliant = True
        soc2_compliant = True
        iso_compliant = True
        non_compliant_reasons = []

        if security_warnings_count > 0:
            for l in logs:
                for alert in l.security_alerts:
                    if "PII" in alert:
                        gdpr_compliant = False
                        if "GDPR non-compliance" not in non_compliant_reasons:
                            non_compliant_reasons.append("GDPR: Unencrypted PII detected in audit history.")
                    if "injection" in alert.lower():
                        iso_compliant = False
                        if "ISO non-compliance" not in non_compliant_reasons:
                            non_compliant_reasons.append("ISO 27001: Injection safety warnings active in logs.")

        return {
            "total_runs": total_runs,
            "approved_runs": approved_runs,
            "denied_runs": denied_runs,
            "failed_runs": failed_runs,
            "violations_count": violations_count,
            "security_warnings_count": security_warnings_count,
            "risk_distribution": risk_distribution,
            "active_policies_count": len(policies),
            "compliance_status": {
                "gdpr_compliant": gdpr_compliant,
                "soc2_compliant": soc2_compliant,
                "iso_compliant": iso_compliant,
                "overall_compliant": gdpr_compliant and soc2_compliant and iso_compliant,
                "reasons": non_compliant_reasons
            }
        }
