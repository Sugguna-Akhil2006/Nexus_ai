"""Optimization report builder generating structured ExecutionOptimizationReport metrics."""

import uuid
from datetime import datetime
from typing import List
from backend.execution_intelligence.models import (
    ExecutionOptimizationReportModel,
    ExecutionMetricsModel,
    BottleneckModel,
    RecommendationModel,
    FailurePredictionModel,
    ResourceOptimizationModel,
)


class OptimizationReport:
    """Aggregates all execution intelligence data into a developer-facing report."""

    @staticmethod
    def generate_report(
        workflow_id: str,
        metrics: ExecutionMetricsModel,
        bottlenecks: List[BottleneckModel],
        suggestions: List[RecommendationModel],
        failures: FailurePredictionModel,
        resources: ResourceOptimizationModel
    ) -> ExecutionOptimizationReportModel:
        """Assembles metrics, detects issues, and computes total savings and speedups."""
        # Calculate estimated savings and speedups
        est_savings = sum(s.estimated_cost_reduction_usd for s in suggestions)
        
        # Max estimated speedup percentage is calculated dynamically based on target recommendations
        speedups = [s.estimated_speedup_pct for s in suggestions if s.estimated_speedup_pct > 0]
        est_gain = max(speedups) if speedups else 0.0

        return ExecutionOptimizationReportModel(
            report_id=f"rep-{uuid.uuid4().hex[:8]}",
            workflow_id=workflow_id,
            timestamp=datetime.utcnow().isoformat(),
            current_metrics=metrics,
            detected_bottlenecks=bottlenecks,
            optimization_suggestions=suggestions,
            failure_prediction=failures,
            resource_recommendations=resources,
            estimated_performance_gain_pct=est_gain,
            estimated_cost_reduction_usd=est_savings
        )
