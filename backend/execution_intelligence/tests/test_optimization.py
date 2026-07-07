"""Tests for bottleneck detection, cost/latency optimization, and recommendation generation."""

import unittest
from backend.execution_intelligence.models import (
    BottleneckType,
    ExecutionMetricsModel,
    ImpactLevel,
    RecommendationCategory,
)
from backend.execution_intelligence.bottleneck_detector import BottleneckDetector
from backend.execution_intelligence.cost_optimizer import CostOptimizer
from backend.execution_intelligence.latency_optimizer import LatencyOptimizer
from backend.execution_intelligence.workflow_recommender import WorkflowRecommender
from backend.runtime.event import EventBus


def reset_event_bus() -> None:
    """Resets the EventBus singleton queue/subscribers between tests."""
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {"published_count": 0, "dispatched_count": 0, "failed_count": 0, "by_type": {}}


def make_metrics(
    workflow_id: str = "wf-test",
    execution_count: int = 10,
    avg_duration_ms: float = 5000.0,
    module_times: dict | None = None,
    retries: int = 0,
    failures: int = 0,
    tokens_in: int = 1000,
    cost_usd: float = 0.05,
    memory_mb: float = 256.0,
    provider_latencies: dict | None = None,
) -> ExecutionMetricsModel:
    return ExecutionMetricsModel(
        workflow_id=workflow_id,
        execution_count=execution_count,
        average_duration_ms=avg_duration_ms,
        total_duration_ms=avg_duration_ms * execution_count,
        module_execution_times=module_times or {},
        retry_counts=retries,
        failures_count=failures,
        total_tokens_in=tokens_in * execution_count,
        estimated_cost_usd=cost_usd * execution_count,
        average_memory_usage_mb=memory_mb,
        provider_latencies=provider_latencies or {},
    )


class TestBottleneckDetection(unittest.TestCase):
    """Validates that BottleneckDetector flags correct conditions."""

    def setUp(self) -> None:
        reset_event_bus()
        self.detector = BottleneckDetector()

    def test_slow_module_detected(self) -> None:
        metrics = make_metrics(
            avg_duration_ms=5000.0,
            module_times={"SlowParser": 50000.0},  # 5000ms avg/run > 40% of 5000ms
        )
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        types = [b.type for b in bottlenecks]
        self.assertIn(BottleneckType.SLOW_MODULE, types)

    def test_high_retry_detected(self) -> None:
        metrics = make_metrics(retries=15, execution_count=10)  # 1.5 avg retries
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        types = [b.type for b in bottlenecks]
        self.assertIn(BottleneckType.HIGH_RETRY, types)

    def test_repeated_failures_detected(self) -> None:
        metrics = make_metrics(failures=4, execution_count=10)  # 40% failure rate
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        types = [b.type for b in bottlenecks]
        self.assertIn(BottleneckType.REPEATED_FAILURES, types)

    def test_expensive_provider_detected(self) -> None:
        metrics = make_metrics(cost_usd=0.25, execution_count=10)  # $0.25/run avg
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        types = [b.type for b in bottlenecks]
        self.assertIn(BottleneckType.EXPENSIVE_PROVIDER, types)

    def test_large_prompts_detected(self) -> None:
        metrics = make_metrics(tokens_in=6000, execution_count=10)  # 6000 avg tokens_in
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        types = [b.type for b in bottlenecks]
        self.assertIn(BottleneckType.LARGE_PROMPTS, types)

    def test_clean_workflow_no_bottlenecks(self) -> None:
        metrics = make_metrics(
            avg_duration_ms=500.0, retries=0, failures=0,
            cost_usd=0.002, tokens_in=200
        )
        bottlenecks = self.detector.detect_bottlenecks(metrics, [])
        self.assertEqual(len(bottlenecks), 0)


class TestCostOptimizer(unittest.TestCase):
    """Validates cost optimization recommendations."""

    def test_high_cost_suggests_downgrade(self) -> None:
        metrics = make_metrics(cost_usd=0.15, execution_count=10)  # $0.15/run avg
        recs = CostOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.ALTERNATIVE_MODELS, categories)

    def test_large_tokens_suggests_caching(self) -> None:
        metrics = make_metrics(tokens_in=5000, execution_count=10)
        recs = CostOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.CACHING_OPPORTUNITIES, categories)

    def test_very_large_tokens_suggests_context_reduction(self) -> None:
        metrics = make_metrics(tokens_in=9000, execution_count=10)
        recs = CostOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.CONTEXT_REDUCTION, categories)

    def test_low_cost_no_recommendations(self) -> None:
        metrics = make_metrics(cost_usd=0.001, tokens_in=100, execution_count=10)
        recs = CostOptimizer.generate_recommendations(metrics)
        self.assertEqual(len(recs), 0)


class TestLatencyOptimizer(unittest.TestCase):
    """Validates latency optimization recommendations."""

    def test_parallel_execution_suggested(self) -> None:
        metrics = make_metrics(
            avg_duration_ms=4000.0,
            module_times={"M1": 5000.0, "M2": 4000.0, "M3": 3000.0},
        )
        recs = LatencyOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.PARALLEL_EXECUTION, categories)

    def test_slow_module_suggests_caching(self) -> None:
        metrics = make_metrics(
            avg_duration_ms=5000.0,
            module_times={"HeavyParser": 25000.0},  # 2500ms avg/run
        )
        recs = LatencyOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.CACHING_OPPORTUNITIES, categories)

    def test_high_latency_provider_suggests_connector_improvement(self) -> None:
        metrics = make_metrics(
            provider_latencies={"anthropic": [5000.0, 6000.0, 4500.0]}
        )
        recs = LatencyOptimizer.generate_recommendations(metrics)
        categories = [r.category for r in recs]
        self.assertIn(RecommendationCategory.CONNECTOR_IMPROVEMENTS, categories)
