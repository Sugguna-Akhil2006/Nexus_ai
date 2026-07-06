"""Top-level AI Observability & Telemetry Platform facade."""

import threading
from datetime import datetime
from typing import Any, Dict, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.observability.cost_tracker import CostTracker
from backend.observability.dashboard_models import (
    AgentTimelineView,
    DashboardView,
    ExecutionTimelineView,
    FailureReportView,
    LatencyChartView,
    TokenUsageView,
)
from backend.observability.event_timeline import EventTimeline
from backend.observability.export_service import ExportService
from backend.observability.metrics_collector import MetricsCollector
from backend.observability.models import (
    ExecutionTrace,
    ExportFormat,
    FailureRecord,
    ModelMetrics,
    SpanStatus,
)
from backend.observability.performance_monitor import PerformanceMonitor
from backend.observability.token_tracker import TokenTracker
from backend.observability.trace_manager import TraceManager


class TelemetryManager:
    """Unified facade for all observability and telemetry capabilities.

    Coordinates trace management, metrics collection, token/cost tracking,
    performance monitoring, event timelines, and export services.
    """

    def __init__(self, latency_threshold_ms: float = 5000.0) -> None:
        self._trace_manager = TraceManager()
        self._metrics_collector = MetricsCollector()
        self._token_tracker = TokenTracker()
        self._cost_tracker = CostTracker()
        self._perf_monitor = PerformanceMonitor(threshold_ms=latency_threshold_ms)
        self._export_service = ExportService()
        self._event_bus = EventBus()

        # per-execution timelines
        self._lock = threading.Lock()
        self._timelines: Dict[str, EventTimeline] = {}

    # ------------------------------------------------------------------
    # Trace lifecycle
    # ------------------------------------------------------------------

    def start_execution_trace(
        self,
        execution_id: str,
        workflow_id: str = "",
        workspace_id: str = "",
    ) -> None:
        """Opens a new trace and publishes ``telemetry.started``.

        Args:
            execution_id: Unique execution identifier.
            workflow_id: Associated workflow (if applicable).
            workspace_id: Originating workspace.
        """
        self._trace_manager.start_trace(execution_id, workflow_id, workspace_id)

        timeline = EventTimeline(execution_id)
        with self._lock:
            self._timelines[execution_id] = timeline
        timeline.append_event("telemetry.started", "Telemetry recording started.")

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="TelemetryManager",
            payload={
                "event": "telemetry.started",
                "execution_id": execution_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))

    def finalize_trace(
        self,
        execution_id: str,
        status: SpanStatus = SpanStatus.COMPLETED,
    ) -> Optional[ExecutionTrace]:
        """Finalises the trace and publishes ``trace.completed`` + ``metrics.updated``.

        Args:
            execution_id: The execution to finalize.
            status: Overall execution outcome.

        Returns:
            The completed ``ExecutionTrace`` or ``None`` if not found.
        """
        trace = self._trace_manager.end_trace(execution_id, status)

        if trace:
            self.append_timeline_event(execution_id, "trace.completed", "Trace finalized.")
            self._event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="TelemetryManager",
                payload={
                    "event": "metrics.updated",
                    "execution_id": execution_id,
                    "duration_ms": trace.total_duration_ms,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            ))

        return trace

    # ------------------------------------------------------------------
    # Span helpers (thin pass-throughs for convenience)
    # ------------------------------------------------------------------

    def start_span(
        self,
        execution_id: str,
        name: str,
        module: str = "",
        parent_span_id: Optional[str] = None,
    ) -> Optional[str]:
        """Opens a span on the active tracer. Returns ``span_id`` or ``None``."""
        tracer = self._trace_manager.get_tracer(execution_id)
        if tracer:
            return tracer.start_span(name, module=module, parent_span_id=parent_span_id)
        return None

    def end_span(
        self,
        execution_id: str,
        span_id: str,
        status: SpanStatus = SpanStatus.COMPLETED,
        error: str = "",
    ) -> None:
        """Closes a span on the active tracer."""
        tracer = self._trace_manager.get_tracer(execution_id)
        if tracer:
            tracer.end_span(span_id, status=status, error=error)

    # ------------------------------------------------------------------
    # Metrics recording
    # ------------------------------------------------------------------

    def record_model_invocation(self, metrics: ModelMetrics) -> None:
        """Records a model invocation and updates token/cost trackers.

        Args:
            metrics: The ``ModelMetrics`` instance to persist.
        """
        self._metrics_collector.record_invocation(metrics)
        self._token_tracker.record_usage(
            metrics.workspace_id, metrics.model, metrics.tokens_in, metrics.tokens_out
        )
        self._cost_tracker.record_cost(
            metrics.workspace_id, metrics.model, metrics.tokens_in, metrics.tokens_out
        )
        self._perf_monitor.record_latency(metrics.model, metrics.latency_ms)

    def record_token_usage(
        self,
        workspace_id: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
    ) -> None:
        """Records raw token consumption without full model metrics."""
        self._token_tracker.record_usage(workspace_id, model, tokens_in, tokens_out)
        self._cost_tracker.record_cost(workspace_id, model, tokens_in, tokens_out)

    def record_failure(self, execution_id: str, record: FailureRecord) -> None:
        """Attaches a failure record to the active trace.

        Args:
            execution_id: The execution where the failure occurred.
            record: The ``FailureRecord`` to persist.
        """
        tracer = self._trace_manager.get_tracer(execution_id)
        if tracer:
            tracer.record_failure(record)
        self.append_timeline_event(
            execution_id,
            "failure.recorded",
            f"{record.exception_type}: {record.message}",
        )

    def append_timeline_event(
        self,
        execution_id: str,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends an event to the execution's timeline.

        Args:
            execution_id: Target execution timeline.
            event_type: Event category label.
            description: Human-readable description.
            metadata: Optional supplemental data.
        """
        with self._lock:
            timeline = self._timelines.get(execution_id)
        if timeline:
            timeline.append_event(event_type, description, metadata)

    # ------------------------------------------------------------------
    # Dashboard & reporting
    # ------------------------------------------------------------------

    def get_dashboard(self, execution_id: str) -> DashboardView:
        """Returns a composite dashboard view for a given execution.

        Args:
            execution_id: The execution to generate a dashboard for.

        Returns:
            A ``DashboardView`` with timeline, latency, token usage and failure data.
        """
        trace = self._trace_manager.get_trace(execution_id)
        with self._lock:
            timeline = self._timelines.get(execution_id)

        events = []
        if timeline:
            events = [e.model_dump() for e in timeline.get_timeline()]

        spans = trace.spans if trace else []
        total_ms = trace.total_duration_ms if trace else 0.0
        agent_ids = trace.agent_ids if trace else []
        failures: list = []

        token_totals = self._token_tracker.get_total_tokens()
        model_breakdown = self._token_tracker.get_model_breakdown()
        snap = self._perf_monitor.get_performance_snapshot()

        return DashboardView(
            execution_timeline=ExecutionTimelineView(
                execution_id=execution_id,
                events=events,
                total_duration_ms=total_ms,
            ),
            agent_timeline=AgentTimelineView(
                execution_id=execution_id,
                agents=[{"agent_id": a} for a in agent_ids],
            ),
            latency_chart=LatencyChartView(
                module_timings=snap.module_timings,
                slowest_operations=snap.slowest_operations,
                avg_latency_ms=snap.avg_latency_ms,
            ),
            token_usage=TokenUsageView(
                total_tokens_in=token_totals["tokens_in"],
                total_tokens_out=token_totals["tokens_out"],
                by_model={m: {"tokens_in": v["tokens_in"], "tokens_out": v["tokens_out"]}
                          for m, v in model_breakdown.items()},
            ),
            failure_report=FailureReportView(
                execution_id=execution_id,
                failures=failures,
                total_failures=len(failures),
            ),
        )

    def get_cost_report(self) -> Dict[str, Any]:
        """Returns full cost breakdown by workspace and model."""
        return self._cost_tracker.get_cost_report()

    def get_provider_stats(self) -> Dict[str, Any]:
        """Returns aggregated model invocation statistics per provider."""
        return self._metrics_collector.get_provider_stats()

    def get_performance_snapshot(self):
        """Returns the current aggregated performance snapshot."""
        return self._perf_monitor.get_performance_snapshot()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_trace(self, execution_id: str, fmt: ExportFormat = ExportFormat.JSON) -> str:
        """Exports a finalized trace in the requested format.

        Args:
            execution_id: The execution whose trace to export.
            fmt: The desired ``ExportFormat``.

        Returns:
            Serialized trace string.

        Raises:
            KeyError: If the trace is not found.
        """
        trace = self._trace_manager.get_trace(execution_id)
        if trace is None:
            raise KeyError(f"No finalized trace for execution '{execution_id}'.")
        return self._export_service.export(trace, fmt)
