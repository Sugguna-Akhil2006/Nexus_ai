"""Tests verifying metric aggregation from traces and model invocations."""

import unittest
from backend.execution_intelligence.execution_analyzer import ExecutionAnalyzer
from backend.observability.models import (
    ExecutionTrace,
    ModelMetrics,
    SpanStatus,
    TraceSpan,
)


def make_trace(
    execution_id: str,
    workflow_id: str,
    duration_ms: float = 2000.0,
    status: SpanStatus = SpanStatus.COMPLETED,
    spans: list[TraceSpan] | None = None,
) -> ExecutionTrace:
    """Factory helper building a minimal ExecutionTrace."""
    t = ExecutionTrace(execution_id=execution_id, workflow_id=workflow_id)
    t.total_duration_ms = duration_ms
    t.status = status
    t.spans = spans or []
    return t


def make_model_metrics(
    execution_id: str,
    provider: str = "openai",
    tokens_in: int = 500,
    tokens_out: int = 200,
    latency_ms: float = 1200.0,
    cost_usd: float = 0.02,
    retries: int = 0,
    failed: bool = False,
) -> ModelMetrics:
    """Factory helper building minimal ModelMetrics."""
    return ModelMetrics(
        execution_id=execution_id,
        workspace_id="ws-test",
        provider=provider,
        model="gpt-4o",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        estimated_cost_usd=cost_usd,
        latency_ms=latency_ms,
        retries=retries,
        failed=failed,
    )


class TestExecutionAnalysis(unittest.TestCase):
    """Verifies that ExecutionAnalyzer correctly aggregates trace metrics."""

    def test_basic_aggregation(self) -> None:
        """Tests counts, totals, and averages from a simple trace set."""
        traces = [
            make_trace("exec-1", "wf-a", duration_ms=2000.0),
            make_trace("exec-2", "wf-a", duration_ms=3000.0),
        ]
        metrics_list = [
            make_model_metrics("exec-1", tokens_in=400, tokens_out=100, cost_usd=0.01, latency_ms=1000.0),
            make_model_metrics("exec-2", tokens_in=600, tokens_out=200, cost_usd=0.03, latency_ms=1500.0),
        ]

        result = ExecutionAnalyzer.analyze_workflow_executions("wf-a", traces, metrics_list)

        self.assertEqual(result.workflow_id, "wf-a")
        self.assertEqual(result.execution_count, 2)
        self.assertAlmostEqual(result.total_duration_ms, 5000.0)
        self.assertAlmostEqual(result.average_duration_ms, 2500.0)
        self.assertEqual(result.total_tokens_in, 1000)
        self.assertEqual(result.total_tokens_out, 300)
        self.assertAlmostEqual(result.estimated_cost_usd, 0.04, places=5)
        self.assertIn("openai", result.provider_latencies)
        self.assertEqual(len(result.provider_latencies["openai"]), 2)

    def test_failure_and_retry_counting(self) -> None:
        """Tests that failures and retry totals are correctly aggregated."""
        traces = [
            make_trace("exec-1", "wf-b", status=SpanStatus.FAILED),
            make_trace("exec-2", "wf-b", status=SpanStatus.COMPLETED),
            make_trace("exec-3", "wf-b", status=SpanStatus.FAILED),
        ]
        metrics_list = [
            make_model_metrics("exec-1", retries=2),
            make_model_metrics("exec-2", retries=0),
            make_model_metrics("exec-3", retries=1),
        ]

        result = ExecutionAnalyzer.analyze_workflow_executions("wf-b", traces, metrics_list)
        self.assertEqual(result.failures_count, 2)
        self.assertEqual(result.retry_counts, 3)

    def test_module_execution_time_aggregation(self) -> None:
        """Tests that span durations are rolled up by module name."""
        span1 = TraceSpan(name="embedding", module="EmbeddingModule", duration_ms=800.0)
        span2 = TraceSpan(name="llm_call", module="LLMModule", duration_ms=2000.0)
        span3 = TraceSpan(name="embedding", module="EmbeddingModule", duration_ms=700.0)

        traces = [
            make_trace("exec-1", "wf-c", spans=[span1, span2]),
            make_trace("exec-2", "wf-c", spans=[span3]),
        ]

        result = ExecutionAnalyzer.analyze_workflow_executions("wf-c", traces, [])
        self.assertIn("EmbeddingModule", result.module_execution_times)
        self.assertIn("LLMModule", result.module_execution_times)
        self.assertAlmostEqual(result.module_execution_times["EmbeddingModule"], 1500.0)
        self.assertAlmostEqual(result.module_execution_times["LLMModule"], 2000.0)

    def test_empty_traces(self) -> None:
        """Tests that zero-trace inputs return zeroed metrics safely."""
        result = ExecutionAnalyzer.analyze_workflow_executions("wf-empty", [], [])
        self.assertEqual(result.execution_count, 0)
        self.assertEqual(result.average_duration_ms, 0.0)
        self.assertEqual(result.total_tokens_in, 0)
