"""Rule compiler transforming declarative rule conditions into executable functions."""

from __future__ import annotations

from typing import Any, Callable, Dict

from backend.policy.models import PolicyRule, RuleCondition


class RuleCompiler:
    """Compiles policy rules with list conditions into fast executable filter checkers."""

    @staticmethod
    def compile_condition(cond: RuleCondition) -> Callable[[Dict[str, Any]], bool]:
        """Translates a condition schema into a callable checker."""
        field = cond.field
        op = cond.operator.lower()
        val = cond.value

        if op == "eq":
            return lambda ctx: ctx.get(field) == val
        if op == "neq":
            return lambda ctx: ctx.get(field) != val
        if op == "gt":
            return lambda ctx: ctx.get(field) is not None and ctx.get(field) > val
        if op == "lt":
            return lambda ctx: ctx.get(field) is not None and ctx.get(field) < val
        if op == "contains":
            return lambda ctx: ctx.get(field) is not None and val in ctx.get(field)
        if op == "in":
            return lambda ctx: ctx.get(field) in val

        return lambda ctx: False

    @classmethod
    def compile_rule(cls, rule: PolicyRule) -> Callable[[Dict[str, Any]], bool]:
        """Compiles all conditions of a rule into a unified AND match checker."""
        checkers = [cls.compile_condition(c) for c in rule.conditions]
        if not checkers:
            # Rule without conditions matches everything
            return lambda ctx: True
        return lambda ctx: all(check(ctx) for check in checkers)
