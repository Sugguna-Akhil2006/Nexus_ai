"""Unit tests for Intelligent Model Router module."""

from __future__ import annotations

import concurrent.futures
import unittest

from backend.platform.models import ModelProfile, ProviderProfile
from backend.providers.router.models import InferenceRequest, RouterExecutionStats
from backend.providers.router.model_router import ModelRouter


class TestModelRouterEngine(unittest.TestCase):
    """Test suite covering dynamic capability matching, weighting policies, and fallback loops."""

    def setUp(self) -> None:
        self.router = ModelRouter()
        self.router.model_mgr.clear()
        self.router.provider_mgr.clear()
        
        # Seed provider profiles
        self.router.provider_mgr.register_provider(ProviderProfile(
            provider_id="openai", name="OpenAI", api_url="https://api.openai.com/v1"
        ))
        self.router.provider_mgr.register_provider(ProviderProfile(
            provider_id="ollama", name="Ollama", api_url="http://localhost:11434"
        ))
        self.router.provider_mgr.register_provider(ProviderProfile(
            provider_id="gemini", name="Google Gemini", api_url="https://gemini.com"
        ))

        # Seed model profiles
        self.router.model_mgr.register_model(ModelProfile(
            model_id="gpt-4", name="GPT-4", provider_id="openai",
            version="1.0", capabilities=["chat", "vision", "reasoning"], is_default=True
        ))
        self.router.model_mgr.register_model(ModelProfile(
            model_id="phi3:mini", name="Phi 3 Mini", provider_id="ollama",
            version="1.0", capabilities=["chat", "local"], is_default=False
        ))
        self.router.model_mgr.register_model(ModelProfile(
            model_id="gemini-1.5", name="Gemini 1.5", provider_id="gemini",
            version="1.5", capabilities=["chat", "vision"], is_default=False
        ))

    def test_routing_policies_selection(self) -> None:
        """Verifies policy weights shift model selection priority."""
        # 1. Low Cost policy should select phi3:mini because cost is 0.0 (local)
        req_cost = InferenceRequest(task_type="chat", policy_preference="cost")
        rec_cost = self.router.route_request(req_cost)
        self.assertEqual(rec_cost.model_id, "phi3:mini")

        # 2. High Quality policy should select gpt-4 because quality index is 95
        req_quality = InferenceRequest(task_type="chat", policy_preference="quality")
        rec_quality = self.router.route_request(req_quality)
        self.assertEqual(rec_quality.model_id, "gpt-4")

    def test_capability_matcher_filtering(self) -> None:
        """Verifies capability requirements prune model selection."""
        # Request requiring 'reasoning' should route only to gpt-4
        req = InferenceRequest(task_type="chat", required_capabilities=["reasoning"])
        rec = self.router.route_request(req)
        self.assertEqual(rec.model_id, "gpt-4")

    def test_fallback_cascade_resolution(self) -> None:
        """Verifies fallback resolving secondary provider."""
        failed_model = self.router.model_mgr.get_model("gpt-4")
        active_models = self.router.model_mgr.list_models()
        
        fallback = self.router.fallback_manager.resolve_fallback(failed_model, active_models)
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback.provider_id, "gemini")

    def test_adaptive_learning_execution_logs(self) -> None:
        """Verifies reporting execution metrics logs history details."""
        stats = RouterExecutionStats(
            model_id="gemini-1.5",
            provider_id="gemini",
            tokens_used=600,
            actual_cost=0.004,
            actual_latency_ms=180.0,
            is_success=True
        )
        self.router.report_execution_metrics(stats)

        # Check predicted latency matches logged average
        pred = self.router.latency_predictor.predict_latency_ms("gemini-1.5")
        self.assertEqual(pred, 180.0)

    def test_concurrent_routing_throughput(self) -> None:
        """Ensures router resolves recommendations concurrently under parallel queries."""
        def run_route(index: int) -> None:
            req = InferenceRequest(task_type="chat", policy_preference="balanced")
            self.router.route_request(req)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_route, i) for i in range(25)]
            concurrent.futures.wait(futures)
