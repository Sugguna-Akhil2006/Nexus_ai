"""Core orchestrator executing workflows and publishing unified execution telemetry."""

import uuid
from typing import Optional

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.state import ExecutionState
from backend.intelligence.core.pipeline import IntelligencePipeline
from backend.intelligence.core.report import IntelligenceExecutionReport


class IntelligenceOrchestrator:
    """Handles pipeline run timing, thread-safe state logging, and EventBus publications."""

    def __init__(self, module_name: str, pipeline: IntelligencePipeline) -> None:
        self.module_name = module_name
        self.pipeline = pipeline
        self.event_bus = EventBus()

    def run(self, context: IntelligenceContext, timeout: Optional[float] = None) -> IntelligenceExecutionReport:
        """Executes the pipeline, maps standard telemetry metrics, and publishes status events.

        Args:
            context: Context containing input settings and intermediate memory state.
            timeout: Optional seconds threshold.

        Returns:
            IntelligenceExecutionReport: Standardized telemetry report.
        """
        exec_id = f"exec-{str(uuid.uuid4())[:8]}"
        state = ExecutionState()

        # Gateway execution started
        self._publish_event("gateway.execution.started", exec_id, context, state)

        # Run pipeline
        self.pipeline.execute(context, state, timeout=timeout)

        # Map pipeline runner outcomes to standard status
        if state.status == "cancelled":
            status = "cancelled"
        elif state.failed_stages and not state.completed_stages:
            status = "failed"
        elif state.failed_stages:
            status = "partial_success"
        else:
            status = "completed"

        state.status = status
        summary = context.intermediate_results.get("output_summary", {})

        report = IntelligenceExecutionReport(
            execution_id=exec_id,
            module_name=self.module_name,
            status=status,
            execution_timeline=state.execution_times,
            stage_results=context.intermediate_results,
            errors=state.errors,
            warnings=state.warnings,
            metrics={"retry_counts": state.retry_counts},
            output_summary=summary
        )

        event_name = "gateway.execution.completed" if status in ["completed", "partial_success"] else "gateway.execution.failed"
        self._publish_event(event_name, exec_id, context, state)

        return report

    def _publish_event(self, event_name: str, exec_id: str, context: IntelligenceContext, state: ExecutionState) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source=f"Orchestrator_{self.module_name}",
            payload={
                "event": event_name,
                "execution_id": exec_id,
                "module": self.module_name,
                "workspace_id": context.workspace_id,
                "status": state.status,
                "completed": state.completed_stages,
                "failed": state.failed_stages,
                "errors": state.errors
            }
        )
        self.event_bus.publish(event)
