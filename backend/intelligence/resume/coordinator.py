"""Workflow coordinator orchestrating stage execution, retries, and events."""

from typing import Callable

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.resume.context import WorkflowContext
from backend.intelligence.resume.state import WorkflowState
from backend.intelligence.resume.workflow import StageNames
from backend.intelligence.resume.pipeline import PipelineExecutionRunner


class WorkflowCoordinator:
    """Orchestrates stage runners, manages retry attempts, and dispatches EventBus signals."""

    def __init__(self, max_retries: int = 3) -> None:
        self.max_retries = max_retries
        self.runner = PipelineExecutionRunner()
        self.event_bus = EventBus()

    def coordinate_execution(self, context: WorkflowContext) -> WorkflowState:
        """Coordinates pipeline stages, collects timings, executes retries, and handles errors.

        Args:
            context: Context containing target documents and intermediate models.

        Returns:
            WorkflowState: Execution logs and telemetry state.
        """
        state = WorkflowState()
        
        # Publish start event
        self._publish_workflow_event("resume.workflow.started", context, state)

        # 1. Ingestion / Parser Stage
        self._execute_with_retry(self.runner.run_parser_stage, context, state, StageNames.PARSER)
        if context.parsed_resume_data:
            self._publish_workflow_event("resume.parser.completed", context, state)

        # 2. Skill Extraction Stage
        self._execute_with_retry(self.runner.run_skills_stage, context, state, StageNames.SKILL_EXTRACTION)
        if context.skill_profile:
            self._publish_workflow_event("resume.skills.completed", context, state)

        # 3. ATS Scoring Stage
        self._execute_with_retry(self.runner.run_ats_stage, context, state, StageNames.ATS_ENGINE)
        if context.ats_report:
            self._publish_workflow_event("resume.ats.completed", context, state)

        # 4. (Optional) JD Matching Stage
        if context.raw_job_description:
            self._execute_with_retry(self.runner.run_jd_stage, context, state, StageNames.JD_MATCHING)
            if context.jd_match_report:
                self._publish_workflow_event("resume.jd.completed", context, state)

        # 5. Analysis Stage
        self._execute_with_retry(self.runner.run_analysis_stage, context, state, StageNames.ANALYSIS)
        if context.analysis_report:
            self._publish_workflow_event("resume.analysis.completed", context, state)

        # 6. Consolidator Stage
        self._execute_with_retry(self.runner.run_consolidation_stage, context, state, StageNames.CONSOLIDATOR)

        # Publish final workflow outcome
        # If the critical parser stage fails and we have no completed stages, the run is failed
        if StageNames.PARSER in state.errors and not state.completed_stages:
            state.pipeline_status = "failed"
            self._publish_workflow_event("resume.workflow.failed", context, state)
        else:
            state.pipeline_status = "completed"
            self._publish_workflow_event("resume.workflow.completed", context, state)

        return state

    def _execute_with_retry(
        self,
        action: Callable[[WorkflowContext, WorkflowState], None],
        context: WorkflowContext,
        state: WorkflowState,
        stage_name: str
    ) -> None:
        attempts = 0
        while attempts < self.max_retries:
            try:
                action(context, state)
                return  # Success
            except Exception as e:
                attempts += 1
                state.record_retry(stage_name)
                if attempts >= self.max_retries:
                    # Final retry exhaustion: mark failure and proceed (graceful degradation)
                    state.fail_stage(stage_name, str(e))
                    return

    def _publish_workflow_event(
        self,
        event_name: str,
        context: WorkflowContext,
        state: WorkflowState
    ) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkflowCoordinator",
            payload={
                "event": event_name,
                "workspace_id": context.workspace_id,
                "document_id": context.document_id,
                "stage": state.current_stage,
                "completed": state.completed_stages,
                "failed_stage": state.failed_stage,
                "retry_counts": state.retry_counts,
                "execution_times": state.execution_times,
                "errors": state.errors
            }
        )
        self.event_bus.publish(event)
