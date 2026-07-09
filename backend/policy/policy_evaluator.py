"""Policy evaluator resolving multi-layered policy rules against context hierarchies."""

from __future__ import annotations

import time
from typing import Any, Dict, List

from backend.policy.models import EvaluationResult, Policy, PolicyDecision
from backend.policy.rule_executor import RuleExecutor


class PolicyEvaluator:
    """Evaluates workspace, organization, provider, and plugin policy chains."""

    @staticmethod
    def evaluate_chain(policies: List[Policy], context: Dict[str, Any]) -> EvaluationResult:
        """Runs the entire chain of policies and yields a final decision.

        Order of enforcement priority:
        1. DENY takes precedence over everything.
        2. WARN triggers warnings but allows action.
        3. AUDIT logs the event without blocking.
        4. ALLOW is the default if no rules match or match allow explicitly.
        """
        start = time.perf_counter()
        matched_rules = []
        warnings = []
        denied_reasons = []
        final_decision = PolicyDecision.ALLOW

        for policy in policies:
            if not policy.enabled:
                continue

            for rule in policy.rules:
                if RuleExecutor.execute(rule, context):
                    matched_rules.append(f"{policy.policy_id}:{rule.rule_id}")

                    if rule.decision == PolicyDecision.DENY:
                        final_decision = PolicyDecision.DENY
                        denied_reasons.append(rule.message or f"Denied by rule: {rule.name}")
                    elif rule.decision == PolicyDecision.WARN:
                        if final_decision != PolicyDecision.DENY:
                            final_decision = PolicyDecision.WARN
                        warnings.append(rule.message or f"Warning from rule: {rule.name}")
                    elif rule.decision == PolicyDecision.AUDIT:
                        if final_decision not in (PolicyDecision.DENY, PolicyDecision.WARN):
                            final_decision = PolicyDecision.AUDIT

        duration = round((time.perf_counter() - start) * 1000, 2)
        return EvaluationResult(
            decision=final_decision,
            matched_rules=matched_rules,
            warnings=warnings,
            denied_reasons=denied_reasons,
            duration_ms=duration,
        )
