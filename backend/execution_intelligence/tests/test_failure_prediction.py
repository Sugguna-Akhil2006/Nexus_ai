"""Tests for failure probability calculations and risk estimations."""

import unittest
from backend.execution_intelligence.failure_predictor import FailurePredictor
from backend.execution_intelligence.models import ExecutionMetricsModel


def make_metrics(
    workflow_id: str = "wf-test",
    execution_count: int = 10,
    failures: int = 0,
    retries: int = 0,
    avg_duration_ms: float = 2000.0,
    avg_memory_mb: float = 256.0,
    provider_latencies: dict | None = None,
) -> ExecutionMetricsModel:
    return ExecutionMetricsModel(
        workflow_id=workflow_id,
        execution_count=execution_count,
        failures_count=failures,
        retry_counts=retries,
        average_duration_ms=avg_duration_ms,
        average_memory_usage_mb=avg_memory_mb,
        provider_latencies=provider_latencies or {},
    )


class TestFailurePrediction(unittest.TestCase):
    """Validates FailurePredictor probability calculations."""

    def test_stable_workflow_has_low_risk(self) -> None:
        """Clean workflow should produce near-zero failure probability."""
        metrics = make_metrics(failures=0, retries=0)
        result = FailurePredictor.predict_failures(metrics)
        self.assertLess(result.failure_probability, 0.15)
        self.assertLess(result.provider_instability_index, 0.3)
        self.assertIn("None detected", result.likely_bottlenecks)

    def test_high_failure_rate_raises_probability(self) -> None:
        """50% failure rate must produce a high failure probability."""
        metrics = make_metrics(failures=5, retries=10, execution_count=10)
        result = FailurePredictor.predict_failures(metrics)
        self.assertGreater(result.failure_probability, 0.5)

    def test_timeout_risk_increases_with_duration(self) -> None:
        """Average duration close to the 10-second threshold must produce high timeout risk."""
        metrics = make_metrics(avg_duration_ms=9000.0)
        result = FailurePredictor.predict_failures(metrics)
        self.assertGreater(result.timeout_risk_pct, 70.0)

    def test_provider_instability_flagged(self) -> None:
        """High average provider latency must increase instability index."""
        metrics = make_metrics(provider_latencies={"openai": [5000.0, 6000.0, 7000.0]})
        result = FailurePredictor.predict_failures(metrics)
        self.assertGreater(result.provider_instability_index, 0.2)
        has_provider_issue = any(
            "Provider" in s or "provider" in s or "timeout" in s.lower() or "retry" in s.lower()
            for s in result.likely_bottlenecks
        )
        self.assertTrue(has_provider_issue)

    def test_resource_exhaustion_grows_with_memory(self) -> None:
        """High memory usage close to the limit must increase exhaustion probability."""
        metrics = make_metrics(avg_memory_mb=450.0)
        result = FailurePredictor.predict_failures(metrics)
        self.assertGreater(result.resource_exhaustion_probability, 0.3)
