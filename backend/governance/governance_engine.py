"""Governance engine orchestrating policies, approvals, validation, and risk assessment."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.governance.models import ComplianceStatus, GovernanceDecision, RiskAssessment
from backend.governance.policy_registry import PolicyRegistry
from backend.governance.execution_guard import ExecutionGuard
from backend.governance.compliance_checker import ComplianceChecker
from backend.governance.audit_logger import AuditLogger


class GovernanceEngine:
    """Central manager orchestrating governance components."""

    def __init__(self) -> None:
        self.registry = PolicyRegistry()
        self.guard = ExecutionGuard()
        self.compliance_checker = ComplianceChecker()
        self.audit_logger = AuditLogger()

    def validate_execution(self, context: Dict[str, Any], payload: Dict[str, Any]) -> GovernanceDecision:
        """Validates execution permissions, security, and policy rules before running.

        Args:
            context: Context containing execution details.
            payload: Payload details.

        Returns:
            GovernanceDecision: Verification details.
        """
        return self.guard.validate_execution(context, payload)

    def assess_payload_risk(self, context: Dict[str, Any], payload: Dict[str, Any]) -> RiskAssessment:
        """Helper to run a risk assessment on a potential execution payload.

        Args:
            context: Context parameters.
            payload: Payload parameters.

        Returns:
            RiskAssessment: The calculated risk metrics.
        """
        sec_res = self.guard.security_validator.validate_payload(payload)
        return self.guard.risk_assessor.assess_risk(context, sec_res)

    def check_compliance_status(self, context: Dict[str, Any], payload: Dict[str, Any]) -> ComplianceStatus:
        """Helper to verify compliance status of a potential execution.

        Args:
            context: Context parameters.
            payload: Payload parameters.

        Returns:
            ComplianceStatus: Compliance metrics summary.
        """
        sec_res = self.guard.security_validator.validate_payload(payload)
        return self.compliance_checker.check_compliance(context, sec_res)

    def get_audit_history(self, workspace_id: Optional[str] = None) -> List[Any]:
        """Retrieves history logs of executed workflows."""
        return self.audit_logger.get_history(workspace_id)
