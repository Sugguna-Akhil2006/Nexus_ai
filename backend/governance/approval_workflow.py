"""Approval workflows determining dynamic execution routing routes."""

from __future__ import annotations

from backend.governance.models import ApprovalType, RiskLevel


class ApprovalWorkflow:
    """Enforces dynamic execution approval workflows based on assessed RiskLevel."""

    def determine_approval_route(self, risk_level: RiskLevel, context: dict) -> ApprovalType:
        """Determines the appropriate approval routing type.

        Args:
            risk_level: Assessed risk classification.
            context: Context details.

        Returns:
            ApprovalType: Required approval type.
        """
        # If execution is a scheduled task/cron, route to scheduled
        if context.get("is_scheduled") or context.get("scheduled_run"):
            return ApprovalType.SCHEDULED

        # Dynamic risk routing
        if risk_level == RiskLevel.CRITICAL:
            return ApprovalType.ADMIN
        elif risk_level == RiskLevel.HIGH:
            return ApprovalType.ADMIN
        elif risk_level == RiskLevel.MEDIUM:
            return ApprovalType.MANUAL
        else:
            return ApprovalType.AUTO
