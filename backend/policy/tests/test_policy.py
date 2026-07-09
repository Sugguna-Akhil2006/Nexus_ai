"""Comprehensive unit and concurrency tests for the Policy Engine."""

from __future__ import annotations

import threading
import unittest

from backend.policy.models import (
    Policy,
    PolicyDecision,
    PolicyRule,
    PolicyType,
    RuleCondition,
)
from backend.policy.policy_engine import PolicyEngine
from backend.policy.rule_compiler import RuleCompiler
from backend.policy.rule_executor import RuleExecutor
from backend.policy.workspace_policy import WorkspacePolicy
from backend.policy.provider_policy import ProviderPolicy
from backend.policy.plugin_policy import PluginPolicy


class TestRuleCompiler(unittest.TestCase):
    """Verifies declarative condition compilation."""

    def test_compile_eq(self) -> None:
        cond = RuleCondition(field="role", operator="eq", value="admin")
        fn = RuleCompiler.compile_condition(cond)
        self.assertTrue(fn({"role": "admin"}))
        self.assertFalse(fn({"role": "user"}))

    def test_compile_gt(self) -> None:
        cond = RuleCondition(field="cost", operator="gt", value=5.0)
        fn = RuleCompiler.compile_condition(cond)
        self.assertTrue(fn({"cost": 5.1}))
        self.assertFalse(fn({"cost": 4.9}))

    def test_compile_lt(self) -> None:
        cond = RuleCondition(field="cost", operator="lt", value=1.0)
        fn = RuleCompiler.compile_condition(cond)
        self.assertTrue(fn({"cost": 0.5}))
        self.assertFalse(fn({"cost": 1.5}))

    def test_compile_contains(self) -> None:
        cond = RuleCondition(field="permissions", operator="contains", value="filesystem")
        fn = RuleCompiler.compile_condition(cond)
        self.assertTrue(fn({"permissions": ["filesystem", "network"]}))
        self.assertFalse(fn({"permissions": ["network"]}))

    def test_compile_in(self) -> None:
        cond = RuleCondition(field="model", operator="in", value=["gpt-4", "claude-3"])
        fn = RuleCompiler.compile_condition(cond)
        self.assertTrue(fn({"model": "gpt-4"}))
        self.assertFalse(fn({"model": "llama-2"}))


class TestRuleExecutor(unittest.TestCase):
    """Verifies rule execution matches conditions context."""

    def test_rule_execution(self) -> None:
        rule = PolicyRule(
            rule_id="r1",
            name="Cost limit",
            decision=PolicyDecision.DENY,
            conditions=[RuleCondition(field="cost", operator="gt", value=10.0)],
        )
        self.assertTrue(RuleExecutor.execute(rule, {"cost": 15.0}))
        self.assertFalse(RuleExecutor.execute(rule, {"cost": 5.0}))


class TestPolicyEngineE2E(unittest.TestCase):
    """Verifies workspace, provider, and plugin policy evaluations and auditing."""

    def setUp(self) -> None:
        self.engine = PolicyEngine()
        self.engine.cleanup()

    def test_workspace_policy_allow(self) -> None:
        wp = WorkspacePolicy.create_default("ws-1")
        self.engine.add_policy(wp)

        res = self.engine.evaluate({"workspace_id": "ws-1", "cost": 1.0})
        self.assertEqual(res.decision, PolicyDecision.ALLOW)

    def test_workspace_policy_warn(self) -> None:
        wp = WorkspacePolicy.create_default("ws-1")
        self.engine.add_policy(wp)

        res = self.engine.evaluate({"workspace_id": "ws-1", "cost": 6.0})
        self.assertEqual(res.decision, PolicyDecision.WARN)
        self.assertEqual(len(res.warnings), 1)

    def test_workspace_policy_deny(self) -> None:
        wp = WorkspacePolicy.create_default("ws-1")
        self.engine.add_policy(wp)

        res = self.engine.evaluate({"workspace_id": "ws-1", "cost": 12.0})
        self.assertEqual(res.decision, PolicyDecision.DENY)
        self.assertEqual(len(res.denied_reasons), 1)

    def test_provider_policy_deny(self) -> None:
        pp = ProviderPolicy.create_default("ollama")
        self.engine.add_policy(pp)

        res = self.engine.evaluate({"workspace_id": "ws-1", "provider": "ollama", "model": "claude-3-opus"})
        self.assertEqual(res.decision, PolicyDecision.DENY)

    def test_plugin_policy_deny(self) -> None:
        pl = PluginPolicy.create_default("plugin-1")
        self.engine.add_policy(pl)

        res = self.engine.evaluate({"workspace_id": "ws-1", "plugin_id": "plugin-1", "permissions": ["filesystem"]})
        self.assertEqual(res.decision, PolicyDecision.DENY)

    def test_statistics_and_audit(self) -> None:
        wp = WorkspacePolicy.create_default("ws-1")
        self.engine.add_policy(wp)

        self.engine.evaluate({"workspace_id": "ws-1", "cost": 12.0})
        self.engine.evaluate({"workspace_id": "ws-1", "cost": 6.0})

        stats = self.engine.get_statistics()
        self.assertEqual(stats["total_evaluations"], 2)
        self.assertEqual(stats["denied_count"], 1)
        self.assertEqual(stats["warning_count"], 1)

        history = self.engine.list_audit_history("ws-1")
        self.assertEqual(len(history), 2)

    def test_thread_safe_evaluations(self) -> None:
        wp = WorkspacePolicy.create_default("ws-1")
        self.engine.add_policy(wp)
        errors = []

        def worker() -> None:
            try:
                self.engine.evaluate({"workspace_id": "ws-1", "cost": 1.0})
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        stats = self.engine.get_statistics()
        self.assertEqual(stats["total_evaluations"], 20)
