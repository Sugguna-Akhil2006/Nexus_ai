"""Tests for thread-safe concurrent execution analysis operations."""

import concurrent.futures
import unittest
from backend.execution_intelligence.optimization_engine import OptimizationEngine
from backend.observability.models import ExecutionTrace, ModelMetrics, SpanStatus
from backend.runtime.event import EventBus


def reset_event_bus() -> None:
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {"published_count": 0, "dispatched_count": 0, "failed_count": 0, "by_type": {}}


def make_trace(exec_id: str, workflow_id: str, duration_ms: float = 1500.0) -> ExecutionTrace:
    t = ExecutionTrace(execution_id=exec_id, workflow_id=workflow_id)
    t.total_duration_ms = duration_ms
    t.status = SpanStatus.COMPLETED
    return t


def make_metrics(exec_id: str) -> ModelMetrics:
    return ModelMetrics(
        execution_id=exec_id,
        workspace_id="ws-concurrent",
        provider="openai",
        model="gpt-4o-mini",
        tokens_in=300,
        tokens_out=100,
        estimated_cost_usd=0.005,
        latency_ms=800.0,
    )


class TestConcurrentExecution(unittest.TestCase):
    """Validates that OptimizationEngine is thread-safe under parallel analysis."""

    def setUp(self) -> None:
        reset_event_bus()

    def test_concurrent_workflow_analyses(self) -> None:
        """Concurrently analyses 20 distinct workflows without data corruption."""
        engine = OptimizationEngine()

        def analyze(wf_index: int) -> str:
            wf_id = f"concurrent-wf-{wf_index}"
            traces = [make_trace(f"exec-{wf_index}-{i}", wf_id, duration_ms=1000.0 + i * 100) for i in range(5)]
            metrics = [make_metrics(f"exec-{wf_index}-{i}") for i in range(5)]
            report = engine.analyze_workflow(wf_id, traces, metrics)
            return report.workflow_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(analyze, range(20)))

        self.assertEqual(len(results), 20)
        all_workflows = engine.list_analyzed_workflows()
        self.assertEqual(len(all_workflows), 20)

        # Verify no cross-contamination
        for i in range(20):
            report = engine.get_optimization_report(f"concurrent-wf-{i}")
            self.assertIsNotNone(report)
            self.assertEqual(report.workflow_id, f"concurrent-wf-{i}")
            self.assertEqual(report.current_metrics.execution_count, 5)

    def test_concurrent_reads_during_analysis(self) -> None:
        """Concurrent reads while an analysis is running must not raise exceptions."""
        engine = OptimizationEngine()

        # Prime a report
        traces = [make_trace("seed-exec", "seed-wf")]
        engine.analyze_workflow("seed-wf", traces, [make_metrics("seed-exec")])

        def read_report(_: int) -> None:
            _ = engine.get_optimization_report("seed-wf")
            _ = engine.get_bottlenecks("seed-wf")
            _ = engine.get_recommendation_history()
            _ = engine.list_analyzed_workflows()

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(read_report, range(30)))
