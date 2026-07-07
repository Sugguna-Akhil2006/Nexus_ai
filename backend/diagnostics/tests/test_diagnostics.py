"""Unit and concurrency tests for the Production Diagnostics & Observability Console."""

from __future__ import annotations

import concurrent.futures
import unittest
from datetime import datetime
from typing import List

from backend.diagnostics.diagnostic_manager import DiagnosticManager
from backend.diagnostics.error_analyzer import ErrorAnalyzer
from backend.diagnostics.models import ErrorCategory, RequestTrace, TimelineStep
from backend.diagnostics.performance_dashboard import PerformanceDashboard
from backend.diagnostics.provider_tracker import ProviderTracker
from backend.diagnostics.request_tracker import RequestTracker
from backend.diagnostics.timeline_builder import TimelineBuilder


class TestRequestTracing(unittest.TestCase):
    """Verifies trace recording and persistence metrics."""

    def setUp(self) -> None:
        self.tracker = RequestTracker()
        self.trace = RequestTrace(
            request_id="req-123",
            workspace_id="ws-99",
            user_id="user-44",
            status="running",
            created_at=datetime.utcnow().isoformat(),
        )

    def test_log_and_get_trace(self) -> None:
        self.tracker.log_trace(self.trace)
        retrieved = self.tracker.get_trace("req-123")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.workspace_id, "ws-99")
        self.assertEqual(retrieved.status, "running")

    def test_list_traces(self) -> None:
        self.tracker.log_trace(self.trace)
        self.assertEqual(len(self.tracker.list_traces()), 1)


class TestTimelineBuilder(unittest.TestCase):
    """Verifies chronological step recording and status changes."""

    def setUp(self) -> None:
        self.builder = TimelineBuilder()

    def test_record_flow(self) -> None:
        self.builder.record_start("ResumeScan", "module")
        steps = self.builder.get_steps()
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].step_name, "ResumeScan")
        self.assertEqual(steps[0].status, "running")

        self.builder.record_completion("ResumeScan", 120.5, {"nodes": 2})
        self.assertEqual(steps[0].status, "completed")
        self.assertEqual(steps[0].duration_ms, 120.5)
        self.assertEqual(steps[0].metadata["nodes"], 2)

    def test_record_failure(self) -> None:
        self.builder.record_start("GitHubScan", "module")
        self.builder.record_failure("GitHubScan", "API Limit Exceeded", 45.2)
        steps = self.builder.get_steps()
        self.assertEqual(steps[0].status, "failed")
        self.assertEqual(steps[0].metadata["error"], "API Limit Exceeded")


class TestErrorAnalyzer(unittest.TestCase):
    """Verifies exception classification mapping."""

    def test_classify_validation_error(self) -> None:
        err = ValueError("Invalid input parameters supplied")
        record = ErrorAnalyzer.classify("req-err", err, "resume")
        self.assertEqual(record.category, ErrorCategory.VALIDATION)
        self.assertEqual(record.module_name, "resume")

    def test_classify_timeout_error(self) -> None:
        err = TimeoutError("Connection to database timed out")
        record = ErrorAnalyzer.classify("req-err", err)
        self.assertEqual(record.category, ErrorCategory.TIMEOUT)

    def test_classify_provider_error(self) -> None:
        err = RuntimeError("Ollama provider is offline")
        record = ErrorAnalyzer.classify("req-err", err)
        self.assertEqual(record.category, ErrorCategory.PROVIDER)


class TestPerformanceDashboard(unittest.TestCase):
    """Verifies metric snap compiling averages."""

    def test_dashboard_compiles_correctly(self) -> None:
        traces = [
            {
                "request_id": "req-1",
                "workspace_id": "ws-1",
                "user_id": "u-1",
                "status": "completed",
                "duration_ms": 100.0,
                "modules_used": [],
                "providers_used": [],
                "retries": 0,
                "errors": {},
                "timeline": [],
                "created_at": "",
            },
            {
                "request_id": "req-2",
                "workspace_id": "ws-1",
                "user_id": "u-2",
                "status": "completed",
                "duration_ms": 200.0,
                "modules_used": [],
                "providers_used": [],
                "retries": 0,
                "errors": {},
                "timeline": [],
                "created_at": "",
            },
        ]
        snap = PerformanceDashboard.get_dashboard_data(traces)
        self.assertEqual(snap["total_requests"], 2)
        self.assertEqual(snap["avg_workflow_duration_ms"], 150.0)
        self.assertEqual(snap["max_workflow_duration_ms"], 200.0)


class TestConcurrentDiagnostics(unittest.TestCase):
    """Verifies thread-safety under simultaneous request tracing."""

    def test_concurrent_provider_logs(self) -> None:
        tracker = ProviderTracker()

        def log_one(idx: int) -> None:
            tracker.log_call(
                provider="openai",
                latency_ms=10.0 + idx,
                tokens_in=100,
                tokens_out=200,
                failed=(idx % 5 == 0),
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(log_one, i) for i in range(1, 51)]
            concurrent.futures.wait(futures)

        summary = tracker.get_summary("openai")
        self.assertIsNotNone(summary)
        self.assertEqual(summary.total_calls, 50)
        self.assertEqual(summary.failures, 10)  # 5, 10, 15, 20, 25, 30, 35, 40, 45, 50 = 10 calls
        self.assertGreater(summary.avg_latency_ms, 0.0)
