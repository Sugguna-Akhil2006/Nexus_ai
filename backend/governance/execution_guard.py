"""Execution guard validating permissions, policies, and security threats prior to execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.governance.models import (
    AuditRecord,
    GovernanceDecision,
    RiskLevel,
    SecurityCheckResult,
    ApprovalType
)
from backend.governance.permission_manager import PermissionManager
from backend.governance.policy_engine import PolicyEngine
from backend.governance.security_validator import SecurityValidator
from backend.governance.risk_assessor import RiskAssessor
from backend.governance.approval_workflow import ApprovalWorkflow
from backend.governance.audit_logger import AuditLogger


class ExecutionGuard:
    """Central gatekeeper intercepting execution requests to validate safety."""

    def __init__(self) -> None:
        self.permission_manager = PermissionManager()
        self.policy_engine = PolicyEngine()
        self.security_validator = SecurityValidator()
        self.risk_assessor = RiskAssessor()
        self.approval_workflow = ApprovalWorkflow()
        self.audit_logger = AuditLogger()
        self.event_bus = EventBus()

    def validate_execution(self, context: Dict[str, Any], payload: Dict[str, Any]) -> GovernanceDecision:
        """Runs security, permissions, policy, and risk checks before executing a workflow.

        Args:
            context: Execution context containing user_id, workspace_id, capability, models, etc.
            payload: Payload of the request.

        Returns:
            GovernanceDecision: Approval state, risk level, routing type, and explanation.
        """
        user_id = context.get("user_id", "admin")
        workspace_id = context.get("workspace_id", "default")
        capability = context.get("capability")

        # Publish Governance start event
        self._publish_event("governance.validation.started", {
            "workspace_id": workspace_id,
            "user_id": user_id,
            "capability": capability
        })

        reasons: List[str] = []
        is_approved = True

        # 1. Validate Permissions
        has_permission = self.permission_manager.check_permission(user_id, workspace_id, capability)
        if not has_permission:
            is_approved = False
            reasons.append("Unauthorized access attempt. User lacks execution rights in workspace.")

        # 2. Validate Security Validator Scans
        security_res = self.security_validator.validate_payload(payload)
        if security_res.warnings:
            self._publish_event("security.warning", {
                "workspace_id": workspace_id,
                "warnings": security_res.warnings
            })
            if security_res.has_prompt_injection or security_res.is_malicious_file:
                is_approved = False
                reasons.extend(security_res.warnings)

        # 3. Validate Policies
        policy_context = {
            "workspace_id": workspace_id,
            "module": capability,
            "model": context.get("model"),
            "provider": context.get("provider"),
            "tokens": context.get("tokens", 0),
            "cost": context.get("cost", 0.0),
            "plugins": context.get("plugins", []),
            "execution_time": context.get("execution_time", 0.0)
        }
        policy_violations = self.policy_engine.evaluate(policy_context)
        if policy_violations:
            is_approved = False
            reasons.extend(policy_violations)

        # 4. Assess Risk level
        risk_res = self.risk_assessor.assess_risk(policy_context, security_res)

        # 5. Determine Approval workflow route
        approval_route = self.approval_workflow.determine_approval_route(risk_res.risk_level, context)

        # Enforce critical risk blockages
        if risk_res.risk_level == RiskLevel.CRITICAL:
            is_approved = False
            reasons.append("Execution blocked: Critical risk score violates guardrails.")

        # Publish decision outcome events
        if is_approved:
            self._publish_event("policy.approved", {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "risk_level": risk_res.risk_level
            })
        else:
            self._publish_event("policy.denied", {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "violations": reasons
            })

        # 6. Persist Audit log entry
        audit_rec = AuditRecord(
            record_id=f"aud-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.utcnow().isoformat(),
            user_id=user_id,
            workspace_id=workspace_id,
            module_used=capability or "unknown",
            model_used=context.get("model") or "unknown",
            provider_used=context.get("provider") or "unknown",
            tokens_consumed=context.get("tokens", 0),
            cost_estimated=context.get("cost", 0.0),
            latency_ms=context.get("execution_time", 0.0) * 1000.0,
            status="approved" if is_approved else "denied",
            policy_violations=policy_violations,
            security_alerts=security_res.warnings,
            risk_level=risk_res.risk_level.value
        )
        self.audit_logger.log_execution(audit_rec)
        self._publish_event("audit.record.created", {"record_id": audit_rec.record_id})

        return GovernanceDecision(
            is_approved=is_approved,
            risk_level=risk_res.risk_level,
            approval_type=approval_route,
            decision_reasons=reasons if reasons else ["Checks passed. Approved automatically."],
            security_check=security_res,
            risk_assessment=risk_res
        )

    def _publish_event(self, event_name: str, payload: dict) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ExecutionGuard",
            payload={
                "event": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                **payload
            }
        )
        self.event_bus.publish(event)
