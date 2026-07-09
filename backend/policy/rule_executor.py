"""Rule executor checking compiled rules against context targets."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.policy.models import PolicyDecision, PolicyRule
from backend.policy.rule_compiler import RuleCompiler


class RuleExecutor:
    """Runs compiled rules against a query context to verify violations."""

    @staticmethod
    def execute(rule: PolicyRule, context: Dict[str, Any]) -> bool:
        """Executes a single rule's compiled condition suite against the context."""
        fn = RuleCompiler.compile_rule(rule)
        try:
            return fn(context)
        except Exception:
            return False
