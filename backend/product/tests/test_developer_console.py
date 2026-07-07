"""Tests for backend.product.developer_console widgets."""

import pytest
from backend.product.developer_console import (
    ExecutionTimeline,
    PipelineStageWidget,
    AgentStatusWidget,
    PerformanceMetricsWidget,
    MemoryUsageWidget,
    ExecutionLogsWidget,
    EventTimelineWidget,
    RequestInspectorWidget,
)


class TestExecutionTimeline:
    def test_build_returns_correct_length(self):
        trace = [
            {"step": "User Request", "status": "Success", "time": "0.01s", "error": ""},
            {"step": "Model Provider", "status": "Success", "time": "0.25s", "error": ""},
        ]
        steps = ExecutionTimeline.build(trace)
        assert len(steps) == 2

    def test_build_assigns_index(self):
        trace = [{"step": "A", "status": "Success", "time": "0.01s", "error": ""}]
        steps = ExecutionTimeline.build(trace)
        assert steps[0]["index"] == 1

    def test_build_marks_error_steps(self):
        trace = [{"step": "Failing Step", "status": "error", "time": "0.01s", "error": "Timeout"}]
        steps = ExecutionTimeline.build(trace)
        assert steps[0]["has_error"] is True

    def test_build_no_error_step(self):
        trace = [{"step": "Good", "status": "success", "time": "0.01s", "error": ""}]
        steps = ExecutionTimeline.build(trace)
        assert steps[0]["has_error"] is False

    def test_build_empty_trace(self):
        assert ExecutionTimeline.build([]) == []

    def test_build_includes_color_and_icon(self):
        trace = [{"step": "S", "status": "success", "time": "0.01s", "error": ""}]
        step = ExecutionTimeline.build(trace)[0]
        assert "color" in step
        assert "icon" in step


class TestPipelineStageWidget:
    def test_build_returns_stages(self):
        timings = {"extraction": "0.042s", "embedding": 0.155, "search": "0.08s"}
        cards = PipelineStageWidget.build(timings)
        assert len(cards) == 3

    def test_build_assigns_bar_pct(self):
        timings = {"fast": "0.01s", "slow": "1.0s"}
        cards = PipelineStageWidget.build(timings)
        slow_card = next(c for c in cards if "Slow" in c["stage"])
        assert slow_card["bar_pct"] == 100.0

    def test_build_empty_timings(self):
        assert PipelineStageWidget.build({}) == []

    def test_build_sorted_by_duration_desc(self):
        timings = {"fast": "0.01s", "slow": "1.0s", "medium": "0.5s"}
        cards = PipelineStageWidget.build(timings)
        durations = [c["duration_ms"] for c in cards]
        assert durations == sorted(durations, reverse=True)


class TestAgentStatusWidget:
    def test_build_returns_agent_map(self):
        states = {
            "ChatAgent": {"status": "success", "task": "Generating"},
            "SearchAgent": {"status": "running", "latency_ms": 42.0},
        }
        result = AgentStatusWidget.build(states)
        assert "ChatAgent" in result
        assert "SearchAgent" in result

    def test_running_agent_is_active(self):
        states = {"SearchAgent": {"status": "running"}}
        result = AgentStatusWidget.build(states)
        assert result["SearchAgent"]["is_active"] is True

    def test_idle_agent_not_active(self):
        states = {"ChatAgent": {"status": "idle"}}
        result = AgentStatusWidget.build(states)
        assert result["ChatAgent"]["is_active"] is False

    def test_build_empty_states(self):
        assert AgentStatusWidget.build({}) == {}


class TestPerformanceMetricsWidget:
    def test_build_from_dict(self):
        data = {
            "avg_duration_ms": 120.5,
            "p95_ms": 400.0,
            "p99_ms": 600.0,
            "error_rate_pct": 2.0,
            "execution_count": 100,
            "avg_tokens": 512.0,
        }
        cards = PerformanceMetricsWidget.build(data)
        assert len(cards) == 6
        labels = [c["label"] for c in cards]
        assert "Avg Latency" in labels
        assert "Error Rate" in labels

    def test_high_error_rate_is_negative_trend(self):
        data = {"error_rate_pct": 25.0}
        cards = PerformanceMetricsWidget.build(data)
        err_card = next(c for c in cards if c["label"] == "Error Rate")
        assert err_card["trend_color"] == "#ef4444"

    def test_low_error_rate_is_positive_trend(self):
        data = {"error_rate_pct": 1.0}
        cards = PerformanceMetricsWidget.build(data)
        err_card = next(c for c in cards if c["label"] == "Error Rate")
        assert err_card["trend_color"] == "#22c55e"

    def test_build_empty_dict_returns_empty(self):
        assert PerformanceMetricsWidget.build({}) == []


class TestMemoryUsageWidget:
    def test_build_returns_correct_keys(self):
        snapshot = {"rss_mb": 200.0, "heap_mb": 150.0, "peak_mb": 250.0}
        result = MemoryUsageWidget.build(snapshot)
        assert result["current_rss_mb"] == 200.0
        assert result["peak_mb"] == 250.0

    def test_high_memory_is_warning(self):
        snapshot = {"rss_mb": 600.0}
        result = MemoryUsageWidget.build(snapshot)
        assert result["status"] == "warning"

    def test_normal_memory_is_healthy(self):
        snapshot = {"rss_mb": 100.0}
        result = MemoryUsageWidget.build(snapshot)
        assert result["status"] == "healthy"


class TestExecutionLogsWidget:
    def _logs(self, n=10):
        return [
            {"timestamp": "2025-01-01T00:00:00Z", "level": "INFO", "message": f"Log entry {i}"}
            for i in range(n)
        ]

    def test_build_paginates_logs(self):
        logs = self._logs(25)
        result = ExecutionLogsWidget.build(logs, page=1, page_size=10)
        assert len(result["rows"]) == 10
        assert result["total"] == 25
        assert result["has_next"] is True

    def test_build_filters_by_level(self):
        logs = [
            {"timestamp": "", "level": "INFO", "message": "info msg"},
            {"timestamp": "", "level": "ERROR", "message": "err msg"},
        ]
        result = ExecutionLogsWidget.build(logs, level="ERROR")
        assert len(result["rows"]) == 1
        assert result["rows"][0]["level"] == "ERROR"

    def test_build_empty_logs(self):
        result = ExecutionLogsWidget.build([])
        assert result["rows"] == []
        assert result["total"] == 0


class TestEventTimelineWidget:
    def test_build_assigns_index(self):
        events = [
            {"timestamp": "T1", "event": "User Message Received"},
            {"timestamp": "T2", "event": "Search Agent triggered"},
        ]
        result = EventTimelineWidget.build(events)
        assert result[0]["index"] == 1
        assert result[1]["index"] == 2

    def test_build_assigns_icons(self):
        events = [{"timestamp": "", "event": "Running model inference"}]
        result = EventTimelineWidget.build(events)
        assert result[0]["icon"] == "🤖"

    def test_build_empty_events(self):
        assert EventTimelineWidget.build([]) == []


class TestRequestInspectorWidget:
    def test_build_detects_diff_keys(self):
        req = {"message": "hello", "workspace_id": "ws-1"}
        resp = {"message": "hi", "tokens": 5}
        result = RequestInspectorWidget.build(req, resp)
        assert "workspace_id" in result["diff_keys"] or "tokens" in result["diff_keys"]
        assert result["has_diff"] is True

    def test_build_no_diff_when_same_keys(self):
        req = {"key": "a"}
        resp = {"key": "b"}
        result = RequestInspectorWidget.build(req, resp)
        assert result["has_diff"] is False

    def test_build_includes_counts(self):
        req = {"a": 1, "b": 2}
        resp = {"x": 1}
        result = RequestInspectorWidget.build(req, resp)
        assert result["request_key_count"] == 2
        assert result["response_key_count"] == 1
