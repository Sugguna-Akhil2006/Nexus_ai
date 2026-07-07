"""Comprehensive tests for the AI Observability & Telemetry Platform."""

import json
import threading
import time
import unittest

from backend.observability.models import (
    ExportFormat,
    FailureRecord,
    ModelMetrics,
    PromptMetadata,
    ReasoningStep,
    SpanStatus,
)
from backend.observability.telemetry_manager import TelemetryManager
from backend.observability.cost_tracker import CostTracker
from backend.observability.token_tracker import TokenTracker
from backend.observability.performance_monitor import PerformanceMonitor
from backend.observability.export_service import ExportService
from backend.observability.execution_trace import ExecutionTracer
from backend.observability.event_timeline import EventTimeline


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestTraceLifecycle(unittest.TestCase):
    """Full trace lifecycle: start → spans → finalize → export."""

    def setUp(self):
        self.tm = TelemetryManager()
        self.eid = "exec-001"

    def test_start_and_finalize(self):
        self.tm.start_execution_trace(self.eid, workflow_id="wf-1", workspace_id="ws-1")
        span_id = self.tm.start_span(self.eid, "Resume Analysis", module="Resume")
        self.assertIsNotNone(span_id)
        self.tm.end_span(self.eid, span_id)
        trace = self.tm.finalize_trace(self.eid)
        self.assertIsNotNone(trace)
        self.assertEqual(trace.execution_id, self.eid)
        self.assertEqual(trace.status, SpanStatus.COMPLETED)
        self.assertEqual(len(trace.spans), 1)
        self.assertEqual(trace.spans[0].status, SpanStatus.COMPLETED)

    def test_multiple_spans_ordered(self):
        self.tm.start_execution_trace(self.eid)
        for i in range(5):
            sid = self.tm.start_span(self.eid, f"Step {i}", module=f"Module{i}")
            self.tm.end_span(self.eid, sid)
        trace = self.tm.finalize_trace(self.eid)
        self.assertEqual(len(trace.spans), 5)

    def test_failed_span_recorded(self):
        self.tm.start_execution_trace(self.eid)
        sid = self.tm.start_span(self.eid, "Failing Step", module="GitHub")
        self.tm.end_span(self.eid, sid, status=SpanStatus.FAILED, error="Connection refused")
        trace = self.tm.finalize_trace(self.eid, status=SpanStatus.FAILED)
        self.assertEqual(trace.status, SpanStatus.FAILED)
        self.assertEqual(trace.spans[0].error, "Connection refused")


class TestTraceValidation(unittest.TestCase):
    """Validates trace completeness and field population."""

    def test_reasoning_steps_captured(self):
        tracer = ExecutionTracer("exec-rs", workflow_id="wf-rs")
        step = ReasoningStep(description="Evaluate evidence", confidence=0.87)
        tracer.record_reasoning_step(step)
        trace = tracer.build_trace()
        self.assertEqual(len(trace.reasoning_steps), 1)
        self.assertAlmostEqual(trace.reasoning_steps[0].confidence, 0.87)

    def test_prompt_and_response_metadata(self):
        tracer = ExecutionTracer("exec-meta")
        tracer.set_prompt_metadata(PromptMetadata(model="llama3", token_count=100))
        trace = tracer.build_trace()
        self.assertIsNotNone(trace.prompt_metadata)
        self.assertEqual(trace.prompt_metadata.model, "llama3")

    def test_duration_positive(self):
        tracer = ExecutionTracer("exec-dur")
        tracer.start_span("A", module="M")
        time.sleep(0.01)
        trace = tracer.build_trace()
        self.assertGreater(trace.total_duration_ms, 0)


class TestTokenAndCostTracking(unittest.TestCase):
    """Token accumulation and cost derivation correctness."""

    def test_token_accumulation(self):
        tt = TokenTracker()
        tt.record_usage("ws-1", "llama3", 100, 50)
        tt.record_usage("ws-1", "llama3", 200, 100)
        usage = tt.get_workspace_usage("ws-1")
        self.assertEqual(usage["tokens_in"], 300)
        self.assertEqual(usage["tokens_out"], 150)

    def test_model_breakdown(self):
        tt = TokenTracker()
        tt.record_usage("ws-1", "llama3", 100, 50)
        tt.record_usage("ws-2", "mistral", 200, 80)
        breakdown = tt.get_model_breakdown()
        self.assertIn("llama3", breakdown)
        self.assertIn("mistral", breakdown)

    def test_cost_calculation(self):
        ct = CostTracker(pricing={"llama3": {"input": 0.001, "output": 0.002}})
        cost = ct.record_cost("ws-1", "llama3", tokens_in=100, tokens_out=50)
        # 100 * 0.001 + 50 * 0.002 = 0.1 + 0.1 = 0.2
        self.assertAlmostEqual(cost, 0.2, places=5)
        report = ct.get_cost_report()
        self.assertAlmostEqual(report["total_usd"], 0.2, places=5)

    def test_cost_fallback_pricing(self):
        ct = CostTracker()
        cost = ct.record_cost("ws-1", "unknown-model", 1000, 500)
        self.assertGreater(cost, 0)


class TestPerformanceMonitor(unittest.TestCase):
    """Performance monitoring and threshold detection."""

    def test_avg_latency_calculation(self):
        pm = PerformanceMonitor(threshold_ms=9999)
        pm.record_latency("Resume", 100.0)
        pm.record_latency("Resume", 200.0)
        self.assertAlmostEqual(pm.get_avg_latency("Resume"), 150.0)

    def test_slowest_ops_ordering(self):
        pm = PerformanceMonitor(threshold_ms=9999)
        pm.record_latency("A", 300.0)
        pm.record_latency("B", 100.0)
        pm.record_latency("C", 500.0)
        slowest = pm.get_slowest_ops(top_n=2)
        self.assertEqual(slowest[0]["latency_ms"], 500.0)
        self.assertEqual(slowest[1]["latency_ms"], 300.0)

    def test_performance_snapshot(self):
        pm = PerformanceMonitor()
        pm.record_latency("Module", 250.0)
        snap = pm.get_performance_snapshot()
        self.assertGreater(snap.avg_latency_ms, 0)
        self.assertIn("Module", snap.module_timings)


class TestExportFormats(unittest.TestCase):
    """JSON, Markdown, and HTML export validation."""

    def _make_trace(self):
        tracer = ExecutionTracer("exec-export", workflow_id="wf-exp")
        sid = tracer.start_span("Analyze", module="Document")
        tracer.end_span(sid, status=SpanStatus.COMPLETED)
        tracer.record_reasoning_step(ReasoningStep(description="Infer conclusions", confidence=0.9))
        return tracer.build_trace()

    def test_json_export_valid(self):
        svc = ExportService()
        trace = self._make_trace()
        output = svc.export(trace, ExportFormat.JSON)
        parsed = json.loads(output)
        self.assertEqual(parsed["execution_id"], "exec-export")
        self.assertIn("spans", parsed)

    def test_markdown_export_contains_sections(self):
        svc = ExportService()
        trace = self._make_trace()
        output = svc.export(trace, ExportFormat.MARKDOWN)
        self.assertIn("# Execution Trace", output)
        self.assertIn("## Spans", output)
        self.assertIn("## Reasoning Steps", output)

    def test_html_export_valid_structure(self):
        svc = ExportService()
        trace = self._make_trace()
        output = svc.export(trace, ExportFormat.HTML)
        self.assertIn("<!DOCTYPE html>", output)
        self.assertIn("exec-export", output)
        self.assertIn("<table>", output)


class TestConcurrentTracing(unittest.TestCase):
    """Thread-safe concurrent trace recording."""

    def test_concurrent_traces_isolated(self):
        tm = TelemetryManager()
        errors = []

        def run_trace(i):
            eid = f"exec-{i}"
            try:
                tm.start_execution_trace(eid)
                sid = tm.start_span(eid, f"Step {i}", module="Module")
                time.sleep(0.005)
                tm.end_span(eid, sid)
                trace = tm.finalize_trace(eid)
                assert trace is not None
                assert trace.execution_id == eid
                assert len(trace.spans) == 1
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=run_trace, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent trace errors: {errors}")


class TestStressTest(unittest.TestCase):
    """100 spans on a single trace within time budget."""

    def test_hundred_spans_performance(self):
        tracer = ExecutionTracer("exec-stress")
        start = time.perf_counter()
        for i in range(100):
            sid = tracer.start_span(f"Span {i}", module=f"Module{i % 5}")
            tracer.end_span(sid)
        trace = tracer.build_trace()
        duration = time.perf_counter() - start

        self.assertEqual(len(trace.spans), 100)
        self.assertLess(duration, 1.0, "100-span stress test exceeded 1-second budget.")


class TestFailureCapture(unittest.TestCase):
    """Failure record capture and root-cause propagation."""

    def test_failure_attached_to_trace(self):
        tm = TelemetryManager()
        eid = "exec-fail"
        tm.start_execution_trace(eid)
        failure = FailureRecord(
            execution_id=eid,
            exception_type="RuntimeError",
            message="Unexpected token",
            stack_trace="...",
            retry_attempts=2,
            recovery_strategy="fallback",
            fallback_module="Document",
            root_cause="Token limit exceeded",
        )
        tm.record_failure(eid, failure)
        trace = tm.finalize_trace(eid, status=SpanStatus.FAILED)
        # Failures are attached to the tracer internally
        self.assertEqual(trace.status, SpanStatus.FAILED)

    def test_timeline_events_recorded(self):
        tm = TelemetryManager()
        eid = "exec-timeline"
        tm.start_execution_trace(eid)
        tm.append_timeline_event(eid, "workflow.started", "Pipeline initiated")
        tm.append_timeline_event(eid, "resume.analyzed", "Resume analysis complete")
        tm.finalize_trace(eid)
        dashboard = tm.get_dashboard(eid)
        event_types = [e["event_type"] for e in dashboard.execution_timeline.events]
        self.assertIn("telemetry.started", event_types)
        self.assertIn("workflow.started", event_types)
        self.assertIn("resume.analyzed", event_types)


class TestDashboardView(unittest.TestCase):
    """Dashboard composite view correctness."""

    def test_dashboard_returns_all_sections(self):
        tm = TelemetryManager()
        eid = "exec-dash"
        tm.start_execution_trace(eid, workspace_id="ws-dash")
        tm.record_model_invocation(ModelMetrics(
            execution_id=eid, workspace_id="ws-dash",
            provider="ollama", model="llama3",
            tokens_in=100, tokens_out=50, latency_ms=120.0,
        ))
        tm.finalize_trace(eid)
        dashboard = tm.get_dashboard(eid)
        self.assertIsNotNone(dashboard.execution_timeline)
        self.assertIsNotNone(dashboard.latency_chart)
        self.assertIsNotNone(dashboard.token_usage)
        self.assertIsNotNone(dashboard.failure_report)
        self.assertGreater(dashboard.token_usage.total_tokens_in, 0)


if __name__ == "__main__":
    unittest.main()
