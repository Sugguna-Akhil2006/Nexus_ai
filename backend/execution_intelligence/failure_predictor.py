"""Failure predictor calculating probabilities for instability, timeouts, and exhaustion."""

from typing import List
from backend.execution_intelligence.models import FailurePredictionModel, ExecutionMetricsModel


class FailurePredictor:
    """Uses historic execution failure rates, latencies, and retries to forecast risks."""

    @staticmethod
    def predict_failures(metrics: ExecutionMetricsModel) -> FailurePredictionModel:
        """Estimates failure probabilities based on previous run metrics."""
        exec_count = metrics.execution_count or 1
        
        # 1. Base Failure Probability
        fail_prob = metrics.failures_count / exec_count

        # Adjust failure probability slightly if there are retries (indicates instability)
        retry_factor = min(0.3, (metrics.retry_counts / exec_count) * 0.1)
        fail_prob = min(0.99, fail_prob + retry_factor)

        # 2. Timeout risk: based on average duration relative to standard thresholds (e.g. 10000ms)
        timeout_risk = min(99.0, max(1.0, (metrics.average_duration_ms / 10000.0) * 100.0))

        # 3. Provider Instability: based on retry rates and average latencies
        provider_instability = 0.05
        if metrics.provider_latencies:
            high_latency_providers = 0
            for latencies in metrics.provider_latencies.values():
                if latencies:
                    avg_lat = sum(latencies) / len(latencies)
                    if avg_lat > 3500:
                        high_latency_providers += 1
            provider_instability = min(0.95, 0.05 + (high_latency_providers * 0.2) + (metrics.retry_counts / exec_count) * 0.15)

        # 4. Resource exhaustion probability: based on memory usage relative to mock limit (e.g. 512MB)
        exhaustion_prob = min(0.99, max(0.01, (metrics.average_memory_usage_mb / 512.0) * 0.5))

        # Find likely bottlenecks
        likely_bottlenecks = []
        if fail_prob > 0.3:
            likely_bottlenecks.append("Frequent runtime failures/exceptions")
        if timeout_risk > 60:
            likely_bottlenecks.append("Execution times close to timeout limit")
        if provider_instability > 0.4:
            likely_bottlenecks.append("Provider network timeouts / retry limits reached")
        elif provider_instability > 0.2:
            likely_bottlenecks.append("Provider latency elevated — potential instability")
        if exhaustion_prob > 0.6:
            likely_bottlenecks.append("Memory usage warning")

        if not likely_bottlenecks:
            likely_bottlenecks.append("None detected")

        return FailurePredictionModel(
            failure_probability=fail_prob,
            likely_bottlenecks=likely_bottlenecks,
            resource_exhaustion_probability=exhaustion_prob,
            timeout_risk_pct=timeout_risk,
            provider_instability_index=provider_instability
        )
