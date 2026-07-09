"""Central Policy Engine coordinator evaluating rules and recording logs."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from backend.policy.audit_logger import AuditLogger
from backend.policy.models import (
    AuditLogEntry,
    EvaluationResult,
    Policy,
    PolicyDecision,
    PolicyType,
)
from backend.policy.policy_evaluator import PolicyEvaluator
from backend.policy.policy_registry import PolicyRegistry


class PolicyEngine:
    """Central decision point coordinating policies registry, evaluation, and auditing.

    Thread Safety:
        Reentrant lock guards evaluation runs and registry updates.
    """

    _instance: Optional["PolicyEngine"] = None

    def __new__(cls) -> "PolicyEngine":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_ready", False):
            return
        self._lock = threading.RLock()
        self._registry = PolicyRegistry()
        self._audit_logger = AuditLogger()
        self._ready = True

    # ------------------------------------------------------------------
    # Policy Management
    # ------------------------------------------------------------------

    def add_policy(self, policy: Policy) -> None:
        """Adds a policy rule block to the engine registry."""
        self._registry.register(policy)

    def remove_policy(self, policy_id: str) -> None:
        """Removes a policy rule from the engine registry."""
        self._registry.remove(policy_id)

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Fetches a policy by ID."""
        return self._registry.get(policy_id)

    def list_policies(self) -> List[Policy]:
        """Returns all registered policies."""
        return self._registry.list_all()

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, context: Dict[str, Any]) -> EvaluationResult:
        """Evaluates all applicable policy rule layers against the query context.

        The evaluation resolves policies applicable to:
        - The specific Workspace target (context['workspace_id'])
        - The specific Organization target (context['organization_id'])
        - The specific Provider target (context['provider'])
        - The specific Plugin target (context['plugin_id'])
        - Global/catch-all targets (*)

        Saves the outcome to the audit log.
        """
        with self._lock:
            # Query applicable policies
            workspace_id = context.get("workspace_id", "default")
            org_id = context.get("organization_id", "default")
            provider = context.get("provider", "*")
            plugin_id = context.get("plugin_id", "*")

            targets = {workspace_id, org_id, provider, plugin_id, "*"}
            applicable: List[Policy] = []
            for target in targets:
                applicable.extend(self._registry.list_target_policies(target) if hasattr(self._registry, "list_target_policies") else self._registry.list_by_target(target))

            # Deduplicate by policy_id
            unique_policies: Dict[str, Policy] = {}
            for p in applicable:
                unique_policies[p.policy_id] = p

            result = PolicyEvaluator.evaluate_chain(list(unique_policies.values()), context)

            # Audit log writing
            self._audit_logger.log(
                user_id=context.get("user_id", "system"),
                workspace_id=workspace_id,
                organization_id=org_id,
                action=context.get("action", "unknown"),
                context=context,
                evaluation=result,
            )

            return result

    # ------------------------------------------------------------------
    # Audit & Observability
    # ------------------------------------------------------------------

    def list_audit_history(self, workspace_id: Optional[str] = None) -> List[AuditLogEntry]:
        """Returns historical audit log records."""
        return self._audit_logger.list_logs(workspace_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Returns policy matching statistics for the developer console."""
        with self._lock:
            logs = self._audit_logger.list_logs()
            total = len(logs)
            denied = sum(1 for log in logs if log.evaluation.decision == PolicyDecision.DENY)
            warnings = sum(1 for log in logs if log.evaluation.decision == PolicyDecision.WARN)

            return {
                "total_evaluations": total,
                "denied_count": denied,
                "warning_count": warnings,
                "active_policies": len(self.list_policies()),
            }

    def cleanup(self) -> None:
        """Clears registry and logs for test runs."""
        with self._lock:
            self._registry.clear()
            self._audit_logger.clear()
