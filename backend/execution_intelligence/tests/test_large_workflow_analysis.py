"""Tests verifying correct analysis of large, complex multi-span workflow traces."""

import unittest
from backend.execution_intelligence.optimization_engine import OptimizationEngine
from backend.observability.models import ExecutionTrace, ModelMetrics, SpanStatus, TraceSpan
from backend.runtime.event import EventBus


def reset_event_bus() -> None:
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {"published_count": 0, "dispatched_count": 0, "failed_count": 0, "by_type": {}}


def build_complex_trace(exec_id: str, workflow_id: str, num_spans: int = 20) -> ExecutionTrace:
    """Creates a trace with many spans including a deliberately slow one."""
    spans = []
    for i in range(num_spans):
        # Make span 0 the "bottleneck" (slow module)
        duration = 5000.0 if i == 0 else 200.0
        spans.append(
            TraceSpan(
                name=f"step_{i}" if i > 0 else "SlowInitializer",
                module=f"Module_{i}" if i > 0 else "SlowModule",
                duration_ms=duration,
            )
        )
    trace = ExecutionTrace(execution_id=exec_id, workflow_id=workflow_id)
    trace.total_duration_ms = sum(s.duration_ms for s in spans)
    trace.status = SpanStatus.COMPLETED
    trace.spans = spans
    return trace


def build_model_metrics(exec_id: str, index: int) -> ModelMetrics:
    return ModelMetrics(
        execution_id=exec_id,
        workspace_id="ws-large",
        provider="openai" if index % 2 == 0 else "anthropic",
        model="gpt-4o",
        tokens_in=6000 + index * 100,  # Large prompts to trigger cost bottleneck
        tokens_out=500,
        estimated_cost_usd=0.12 + index * 0.01,
        latency_ms=1500.0 + index * 50,
        retries=index % 3,
    )


class TestLargeWorkflowAnalysis(unittest.TestCase):
    """Validates that OptimizationEngine scales correctly for complex workflow analysis."""

    def setUp(self) -> None:
        reset_event_bus()

    def test_large_multi_span_workflow(self) -> None:
        """Analysing 50 executions with 20 spans each must produce correct bottlenecks."""
        engine = OptimizationEngine()
        wf_id = "large-wf"
        traces = [build_complex_trace(f"exec-{i}", wf_id, num_spans=20) for i in range(50)]
        metrics = [build_model_metrics(f"exec-{i}", i) for i in range(50)]

        report = engine.analyze_workflow(wf_id, traces, metrics)

        # Should have found the slow module
        self.assertGreater(len(report.detected_bottlenecks), 0)
        bn_types = [b.type.value for b in report.detected_bottlenecks]
        self.assertIn("Slow Module", bn_types)

        # Large prompts bottleneck expected
        self.assertIn("Large Prompts", bn_types)

        # Should have generated recommendations
        self.assertGreater(len(report.optimization_suggestions), 0)

        # Module execution times must include all unique modules
        self.assertEqual(report.current_metrics.execution_count, 50)
        self.assertIn("SlowModule", report.current_metrics.module_execution_times)

    def test_high_span_count_does_not_crash(self) -> None:
        """Stress test: 100 spans per trace, 30 executions."""
        engine = OptimizationEngine()
        wf_id = "stress-wf"
        traces = [build_complex_trace(f"exec-stress-{i}", wf_id, num_spans=100) for i in range(30)]
        metrics = [build_model_metrics(f"exec-stress-{i}", i) for i in range(30)]

        # Should not raise
        report = engine.analyze_workflow(wf_id, traces, metrics)
        self.assertIsNotNone(report)
        self.assertEqual(report.current_metrics.execution_count, 30)

    def test_console_display_data_scales(self) -> None:
        """Console display must return correct structure even with many workflows."""
        engine = OptimizationEngine()
        for wf_idx in range(10):
            wf_id = f"scale-wf-{wf_idx}"
            traces = [build_complex_trace(f"exec-{wf_idx}-{i}", wf_id) for i in range(5)]
            metrics = [build_model_metrics(f"exec-{wf_idx}-{i}", i) for i in range(5)]
            engine.analyze_workflow(wf_id, traces, metrics)

        console = engine.get_console_display_data(top_n=5)
        self.assertIn("top_bottlenecks", console)
        self.assertIn("optimization_opportunities", console)
        self.assertIn("workflow_rankings", console)
        self.assertIn("module_efficiency", console)
        self.assertLessEqual(len(console["top_bottlenecks"]), 5)
        self.assertLessEqual(len(console["module_efficiency"]), 5)
