"""Optimization engine orchestrating all analysis subsystems and exposing the unified API."""

import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.execution_intelligence.bottleneck_detector import BottleneckDetector
from backend.execution_intelligence.execution_analyzer import ExecutionAnalyzer
from backend.execution_intelligence.failure_predictor import FailurePredictor
from backend.execution_intelligence.models import (
    BottleneckModel,
    ExecutionMetricsModel,
    ExecutionOptimizationReportModel,
    RecommendationModel,
)
from backend.execution_intelligence.optimization_report import OptimizationReport
from backend.execution_intelligence.resource_optimizer import ResourceOptimizer
from backend.execution_intelligence.workflow_recommender import WorkflowRecommender
from backend.observability.models import ExecutionTrace, ModelMetrics
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class OptimizationEngine:
    """Unified entry point for AI Execution Intelligence & Optimization analysis.

    Coordinates execution analysis, bottleneck detection, failure prediction,
    resource optimization, workflow recommendations, and report generation.
    All subsystem calls are read-only. The engine never modifies workflows.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._event_bus = EventBus()
        self._analyzer = ExecutionAnalyzer()
        self._bottleneck_detector = BottleneckDetector()
        self._recommender = WorkflowRecommender()
        self._failure_predictor = FailurePredictor()
        self._resource_optimizer = ResourceOptimizer()

        # In-memory history stores
        self._reports: Dict[str, ExecutionOptimizationReportModel] = {}  # workflow_id -> latest report
        self._recommendation_history: List[RecommendationModel] = []

    # ------------------------------------------------------------------
    # Primary Analysis API
    # ------------------------------------------------------------------

    def analyze_workflow(
        self,
        workflow_id: str,
        traces: List[ExecutionTrace],
        model_metrics: List[ModelMetrics],
    ) -> ExecutionOptimizationReportModel:
        """Runs the full optimization analysis pipeline for a specific workflow.

        Args:
            workflow_id: Target workflow identifier.
            traces: Completed execution traces from the Observability Platform.
            model_metrics: Model invocation metrics from MetricsCollector.

        Returns:
            ExecutionOptimizationReportModel: Full structured report.
        """
        with self._lock:
            # Publish analysis started event
            self._event_bus.publish(Event(
                event_type=EventType.OPTIMIZATION_ANALYSIS_STARTED,
                priority=EventPriority.NORMAL,
                payload={
                    "workflow_id": workflow_id,
                    "trace_count": len(traces),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ))

            # Step 1 – Aggregate metrics from traces
            metrics = ExecutionAnalyzer.analyze_workflow_executions(
                workflow_id, traces, model_metrics
            )

            # Step 2 – Detect bottlenecks
            bottlenecks = self._bottleneck_detector.detect_bottlenecks(metrics, traces)

            # Step 3 – Generate recommendations
            recommendations = self._recommender.generate_all_recommendations(metrics)
            self._recommendation_history.extend(recommendations)

            # Step 4 – Predict failures
            failure_prediction = FailurePredictor.predict_failures(metrics)

            # Step 5 – Resource recommendations
            resource_recs = ResourceOptimizer.recommend_resources(metrics)

            # Step 6 – Compile report
            report = OptimizationReport.generate_report(
                workflow_id=workflow_id,
                metrics=metrics,
                bottlenecks=bottlenecks,
                suggestions=recommendations,
                failures=failure_prediction,
                resources=resource_recs,
            )
            self._reports[workflow_id] = report

            # Publish analysis completed event
            self._event_bus.publish(Event(
                event_type=EventType.OPTIMIZATION_COMPLETED,
                priority=EventPriority.NORMAL,
                payload={
                    "workflow_id": workflow_id,
                    "report_id": report.report_id,
                    "bottlenecks_found": len(bottlenecks),
                    "recommendations_count": len(recommendations),
                    "estimated_performance_gain_pct": report.estimated_performance_gain_pct,
                    "estimated_cost_reduction_usd": report.estimated_cost_reduction_usd,
                },
            ))

            return report

    # ------------------------------------------------------------------
    # Query APIs
    # ------------------------------------------------------------------

    def get_optimization_report(self, workflow_id: str) -> Optional[ExecutionOptimizationReportModel]:
        """Returns the latest optimization report for a workflow."""
        with self._lock:
            return self._reports.get(workflow_id)

    def get_execution_metrics(self, workflow_id: str) -> Optional[ExecutionMetricsModel]:
        """Returns the current aggregated execution metrics for a workflow."""
        with self._lock:
            report = self._reports.get(workflow_id)
            return report.current_metrics if report else None

    def get_bottlenecks(self, workflow_id: str) -> List[BottleneckModel]:
        """Returns detected bottlenecks for a workflow."""
        with self._lock:
            report = self._reports.get(workflow_id)
            return report.detected_bottlenecks if report else []

    def get_recommendation_history(self) -> List[RecommendationModel]:
        """Returns all recommendations generated across all workflow analyses."""
        with self._lock:
            return list(self._recommendation_history)

    def list_analyzed_workflows(self) -> List[str]:
        """Returns all workflow IDs that have been analysed."""
        with self._lock:
            return list(self._reports.keys())

    # ------------------------------------------------------------------
    # Developer Console Display
    # ------------------------------------------------------------------

    def get_console_display_data(self, top_n: int = 5) -> Dict[str, Any]:
        """Compiles structured data for the developer console dashboard.

        Args:
            top_n: Number of top bottlenecks and workflow rankings to display.

        Returns:
            Dict containing bottlenecks, opportunities, workflow rankings,
            module efficiencies, and recommendation history.
        """
        with self._lock:
            # Aggregate all bottlenecks and rank by impact
            all_bottlenecks: List[BottleneckModel] = []
            workflow_rankings: List[Dict[str, Any]] = []
            all_module_times: Dict[str, float] = {}

            _impact_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

            for wf_id, report in self._reports.items():
                all_bottlenecks.extend(report.detected_bottlenecks)

                # Workflow ranking
                workflow_rankings.append({
                    "workflow_id": wf_id,
                    "avg_duration_ms": report.current_metrics.average_duration_ms,
                    "failures": report.current_metrics.failures_count,
                    "estimated_cost_usd": report.current_metrics.estimated_cost_usd,
                    "estimated_gain_pct": report.estimated_performance_gain_pct,
                    "bottleneck_count": len(report.detected_bottlenecks),
                })

                # Module efficiency aggregation
                for mod, ms in report.current_metrics.module_execution_times.items():
                    all_module_times[mod] = all_module_times.get(mod, 0.0) + ms

            # Sort bottlenecks by impact level
            top_bottlenecks = sorted(
                all_bottlenecks,
                key=lambda b: _impact_order.get(b.impact_level.value, 99),
            )[:top_n]

            # Sort workflow rankings by failure count + bottleneck count
            workflow_rankings.sort(key=lambda w: (w["failures"], w["bottleneck_count"]), reverse=True)

            # Module efficiency: slowest modules first
            module_efficiency = sorted(
                [{"module": m, "total_ms": ms} for m, ms in all_module_times.items()],
                key=lambda x: x["total_ms"],
                reverse=True,
            )[:top_n]

            return {
                "top_bottlenecks": [b.model_dump() for b in top_bottlenecks],
                "optimization_opportunities": [
                    r.model_dump() for r in self._recommendation_history[:top_n]
                ],
                "workflow_rankings": workflow_rankings,
                "module_efficiency": module_efficiency,
                "recommendation_history_count": len(self._recommendation_history),
            }
