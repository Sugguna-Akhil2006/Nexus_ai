"""Tests for backend.product.metrics_service."""

import pytest
import time
from backend.product.metrics_service import MetricsService


@pytest.fixture(autouse=True)
def clean_metrics():
    """Reset metrics state before each test."""
    MetricsService().clear()
    yield
    MetricsService().clear()


class TestMetricsServiceSingleton:
    def test_singleton_returns_same_instance(self):
        a = MetricsService()
        b = MetricsService()
        assert a is b


class TestExecutionRecording:
    def test_start_execution_returns_id(self):
        svc = MetricsService()
        exec_id = svc.start_execution("test_pipeline")
        assert exec_id.startswith("exec-")

    def test_record_stage_returns_true_for_valid_execution(self):
        svc = MetricsService()
        exec_id = svc.start_execution("pipeline_a")
        result = svc.record_stage(exec_id, stage="parsing", duration_ms=42.0)
        assert result is True

    def test_record_stage_returns_false_for_invalid_execution(self):
        svc = MetricsService()
        result = svc.record_stage("nonexistent", stage="any", duration_ms=1.0)
        assert result is False

    def test_finish_execution_returns_record(self):
        svc = MetricsService()
        exec_id = svc.start_execution("pipeline_b")
        svc.record_stage(exec_id, "embed", 100.0)
        record = svc.finish_execution(exec_id, success=True, total_tokens=512)
        assert record is not None
        assert record.success is True
        assert record.total_tokens == 512

    def test_finish_nonexistent_execution_returns_none(self):
        svc = MetricsService()
        result = svc.finish_execution("bad-id")
        assert result is None

    def test_total_duration_is_computed(self):
        svc = MetricsService()
        exec_id = svc.start_execution("pipeline_dur")
        time.sleep(0.05)
        record = svc.finish_execution(exec_id)
        assert record.total_duration_ms > 0


class TestAggregation:
    def _run_pipeline(self, svc: MetricsService, pipeline: str, duration_ms: float, success: bool = True):
        """Helper to simulate a full pipeline execution."""
        exec_id = svc.start_execution(pipeline)
        svc.record_stage(exec_id, "stage1", duration_ms * 0.4)
        svc.record_stage(exec_id, "stage2", duration_ms * 0.6)
        svc.finish_execution(exec_id, success=success, total_tokens=100)

    def test_get_pipeline_metrics_returns_aggregates(self):
        svc = MetricsService()
        for _ in range(5):
            self._run_pipeline(svc, "resume_analysis", 200.0)
        metrics = svc.get_pipeline_metrics("resume_analysis")
        assert metrics is not None
        assert metrics.execution_count == 5
        assert metrics.success_count == 5
        assert metrics.error_count == 0
        assert metrics.p50_ms >= 0
        assert metrics.p95_ms >= metrics.p50_ms

    def test_get_pipeline_metrics_returns_none_for_unknown(self):
        svc = MetricsService()
        result = svc.get_pipeline_metrics("unknown_pipeline")
        assert result is None

    def test_error_rate_computed_correctly(self):
        svc = MetricsService()
        for _ in range(8):
            self._run_pipeline(svc, "mixed", 100.0, success=True)
        for _ in range(2):
            self._run_pipeline(svc, "mixed", 100.0, success=False)
        metrics = svc.get_pipeline_metrics("mixed")
        assert abs(metrics.error_rate_pct - 20.0) < 1.0

    def test_performance_snapshot_covers_all_pipelines(self):
        svc = MetricsService()
        self._run_pipeline(svc, "pipe_x", 100.0)
        self._run_pipeline(svc, "pipe_y", 200.0)
        snapshot = svc.get_performance_snapshot()
        assert snapshot.total_executions == 2
        assert "pipe_x" in snapshot.pipeline_metrics
        assert "pipe_y" in snapshot.pipeline_metrics

    def test_list_pipelines_returns_recorded_names(self):
        svc = MetricsService()
        self._run_pipeline(svc, "list_test", 50.0)
        pipelines = svc.list_pipelines()
        assert "list_test" in pipelines

    def test_stage_avg_ms_populated(self):
        svc = MetricsService()
        for _ in range(3):
            self._run_pipeline(svc, "stage_test", 300.0)
        metrics = svc.get_pipeline_metrics("stage_test")
        assert "stage1" in metrics.stage_avg_ms
        assert "stage2" in metrics.stage_avg_ms
        assert metrics.stage_avg_ms["stage1"] > 0

    def test_rolling_window_does_not_grow_unbounded(self):
        svc = MetricsService()
        for _ in range(510):  # exceed _WINDOW_SIZE = 500
            self._run_pipeline(svc, "overflow", 10.0)
        metrics = svc.get_pipeline_metrics("overflow")
        assert metrics.execution_count <= 500
