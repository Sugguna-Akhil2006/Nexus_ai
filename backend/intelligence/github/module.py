"""GitHub Intelligence module implementation conforming to core base framework."""

import time
from typing import Set, Dict, Any

from backend.intelligence.core.base_intelligence import BaseIntelligenceModule
from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.report import IntelligenceExecutionReport
from backend.intelligence.github.github_agent import GitHubAgent


class GitHubModule(BaseIntelligenceModule):
    """GitHub Intelligence adapter subclassing BaseIntelligenceModule for global orchestration."""

    @property
    def name(self) -> str:
        return "GitHubIntelligence"

    @property
    def capabilities(self) -> Set[str]:
        return {"GITHUB_REPO_ANALYSIS", "GITHUB_QUALITY_AUDIT", "GITHUB_ACTIVITY_HEALTH", "GITHUB_INTELLIGENCE"}

    def execute_workflow(self, context: IntelligenceContext) -> IntelligenceExecutionReport:
        """Executes the GitHub Intelligence workflow on the context.

        Args:
            context: Context details.

        Returns:
            IntelligenceExecutionReport: Consolidated telemetry report.
        """
        agent = GitHubAgent()
        start_time = time.perf_counter()

        workspace_path = context.metadata.get("workspace_path") or "."
        workspace_id = context.workspace_id
        repository_url = context.metadata.get("repository_url") or ""
        branch = context.metadata.get("branch") or "main"

        try:
            results = agent.run_analysis(
                workspace_path=workspace_path,
                workspace_id=workspace_id,
                repository_url=repository_url,
                branch=branch
            )

            # Store outputs in context intermediate results
            context.intermediate_results["github_repo_report"] = results.get("repo_report")
            context.intermediate_results["github_quality_report"] = results.get("quality_report")
            context.intermediate_results["github_health_report"] = results.get("health_report")

            duration = time.perf_counter() - start_time
            timeline = {
                "total_duration": duration,
                "analysis": duration * 0.4,
                "quality": duration * 0.3,
                "health": duration * 0.3
            }

            # Map report outputs
            output_summary = {
                "repository_url": repository_url,
                "branch": branch,
                "file_count": results.get("repo_report").file_count if results.get("repo_report") else 0,
                "maintainability_score": results.get("quality_report").maintainability_score if results.get("quality_report") else 0.0,
                "overall_health_score": results.get("health_report").health_scores.overall_health_score if results.get("health_report") else 0.0
            }

            return IntelligenceExecutionReport(
                execution_id=context.document_ids[0] if context.document_ids else "exec-github",
                module_name=self.name,
                status="completed",
                execution_timeline=timeline,
                stage_results={
                    "repo_report": results.get("repo_report").model_dump() if results.get("repo_report") else {},
                    "quality_report": results.get("quality_report").model_dump() if results.get("quality_report") else {},
                    "health_report": results.get("health_report").model_dump() if results.get("health_report") else {}
                },
                errors={},
                warnings={},
                metrics={
                    "file_count": output_summary["file_count"],
                    "total_commits": results.get("health_report").total_commits if results.get("health_report") else 0
                },
                output_summary=output_summary
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            return IntelligenceExecutionReport(
                execution_id="exec-github",
                module_name=self.name,
                status="failed",
                execution_timeline={"total_duration": duration},
                stage_results={},
                errors={"workflow": str(e)},
                warnings={},
                metrics={},
                output_summary={}
            )
