"""Unit tests for AI Platform Operations Center module."""

from __future__ import annotations

import concurrent.futures
import unittest

from backend.platform.models import ModelProfile, ProviderProfile, QuotaPolicy
from backend.platform.platform_manager import PlatformManager


class TestPlatformOperations(unittest.TestCase):
    """Test suite covering model managers, routing, quotas, and failovers."""

    def setUp(self) -> None:
        self.mgr = PlatformManager()
        self.mgr.provider_mgr.clear()
        self.mgr.model_mgr.clear()
        self.mgr.quota_mgr.clear()
        self.mgr.analytics.clear()

        # Seed test profiles
        self.mgr.provider_mgr.register_provider(ProviderProfile(
            provider_id="openai", name="OpenAI", api_url="https://api.openai.com/v1"
        ))
        self.mgr.provider_mgr.register_provider(ProviderProfile(
            provider_id="gemini", name="Google Gemini", api_url="https://gemini.com"
        ))
        self.mgr.provider_mgr.register_provider(ProviderProfile(
            provider_id="ollama", name="Ollama", api_url="http://localhost:11434"
        ))

        self.mgr.model_mgr.register_model(ModelProfile(
            model_id="gpt-4", name="GPT-4", provider_id="openai",
            version="1.0", capabilities=["chat", "extraction"], is_default=True
        ))
        self.mgr.model_mgr.register_model(ModelProfile(
            model_id="phi3", name="Phi 3", provider_id="ollama",
            version="1.0", capabilities=["chat", "local"], is_default=False
        ))

    def test_routing_engine_decisions(self) -> None:
        """Verifies task capabilities filter model selections."""
        # 1. Routing for extraction task should select gpt-4
        route = self.mgr.routing_engine.select_route("extraction", "ws-test")
        self.assertEqual(route.model_id, "gpt-4")

        # 2. Routing for local task should select phi3
        route_local = self.mgr.routing_engine.select_route("local", "ws-test")
        self.assertEqual(route_local.model_id, "phi3")

    def test_provider_failover_recovery(self) -> None:
        """Verifies failover detects degraded providers and updates routing."""
        # Force failover from openai to gemini
        fallback_id = self.mgr.failover_mgr.trigger_provider_failure("openai")
        self.assertEqual(fallback_id, "gemini")

        # Provider should report degraded health status
        prov = self.mgr.provider_mgr.get_provider("openai")
        self.assertEqual(prov.health_status, "degraded")

    def test_quota_limits_checking(self) -> None:
        """Verifies that exceeding daily token caps throws errors."""
        policy = QuotaPolicy(
            policy_id="policy-test",
            workspace_id="ws-test",
            daily_token_limit=1000,
            daily_cost_limit=10.0
        )
        self.mgr.quota_mgr.set_quota_policy(policy)

        # 1. First execution within limits
        ok = self.mgr.quota_mgr.check_and_record_consumption("ws-test", "user-1", tokens=800, cost=2.0)
        self.assertTrue(ok)

        # 2. Second execution breaches cap
        fail = self.mgr.quota_mgr.check_and_record_consumption("ws-test", "user-1", tokens=300, cost=1.0)
        self.assertFalse(fail)

    def test_analytics_logging_metrics(self) -> None:
        """Verifies request logging counts and dashboard aggregates."""
        self.mgr.analytics.log_request("gpt-4", "openai", tokens=500, cost=0.015, latency_ms=120.0, status="success")
        self.mgr.analytics.log_request("phi3", "ollama", tokens=200, cost=0.0, latency_ms=45.0, status="success")

        summary = self.mgr.analytics.get_metrics_summary()
        self.assertEqual(summary.total_requests, 2)
        self.assertEqual(summary.total_tokens, 700)

        dash = self.mgr.get_admin_dashboard_metrics()
        self.assertEqual(dash["usage_summary"]["total_requests"], 2)

    def test_concurrent_quota_locks(self) -> None:
        """Ensures quota consumption handles parallel threads securely."""
        policy = QuotaPolicy(
            policy_id="policy-concurrent",
            workspace_id="ws-concurrent",
            daily_token_limit=50000,
            daily_cost_limit=100.0
        )
        self.mgr.quota_mgr.set_quota_policy(policy)

        def run_thread(index: int) -> None:
            self.mgr.quota_mgr.check_and_record_consumption("ws-concurrent", f"user-{index}", tokens=100, cost=0.01)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
