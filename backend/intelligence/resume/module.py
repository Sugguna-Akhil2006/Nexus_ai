"""Resume Intelligence module implementation conforming to core base framework."""

from typing import Set

from backend.intelligence.core.base_intelligence import BaseIntelligenceModule
from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.report import IntelligenceExecutionReport
from backend.intelligence.resume.resume_agent import ResumeAgent


class ResumeModule(BaseIntelligenceModule):
    """Resume Intelligence adapter subclassing BaseIntelligenceModule for global orchestration."""

    @property
    def name(self) -> str:
        return "ResumeIntelligence"

    @property
    def capabilities(self) -> Set[str]:
        return {"RESUME_PARSING", "ATS_ANALYSIS", "SKILL_EXTRACTION", "JD_MATCHING"}

    def execute_workflow(self, context: IntelligenceContext) -> IntelligenceExecutionReport:
        """Executes the Resume Intelligence workflow on the context.

        Args:
            context: Context details.

        Returns:
            IntelligenceExecutionReport: Consolidated telemetry report.
        """
        agent = ResumeAgent()

        # Map metadata inputs
        resume_data = context.metadata.get("resume")
        job_description = context.metadata.get("job_description")
        workspace_id = context.workspace_id
        document_id = context.document_ids[0] if context.document_ids else None
        filename = context.metadata.get("filename", "resume.txt")

        # Run the existing agent orchestration
        unified_report = agent.analyze_resume(
            resume=resume_data,
            job_description=job_description,
            workspace_id=workspace_id,
            document_id=document_id,
            filename=filename
        )

        # Store output result in context
        context.intermediate_results["unified_report"] = unified_report

        # Extract telemetry details
        timeline = unified_report.execution_metrics.get("execution_times", {})
        metrics = {"retry_counts": unified_report.execution_metrics.get("retry_counts", {})}
        errors = unified_report.pipeline_metadata.get("errors", {})
        
        # Build Standard IntelligenceExecutionReport
        return IntelligenceExecutionReport(
            execution_id=unified_report.pipeline_metadata.get("document_id", "exec-default"),
            module_name=self.name,
            status=unified_report.pipeline_metadata.get("pipeline_status", "completed"),
            execution_timeline=timeline,
            stage_results={"unified_report": unified_report.model_dump()},
            errors=errors,
            warnings={},
            metrics=metrics,
            output_summary=unified_report.resume_summary or {}
        )
