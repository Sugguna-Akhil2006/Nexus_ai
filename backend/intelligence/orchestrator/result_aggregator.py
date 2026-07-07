"""Result aggregator merging multi-module outputs, citations, and confidence scores."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.intelligence.contracts.response_models import Artifact, Citation, Recommendation
from backend.intelligence.orchestrator.execution_context import OrchestrationContext
from backend.intelligence.orchestrator.models import ExecutionGraph, OrchestratedResult


class ResultAggregator:
    """Consolidates execution outcomes, timing logs, and errors into a final report."""

    @staticmethod
    def aggregate(
        request_id: str,
        plan_id: str,
        graph: ExecutionGraph,
        ctx: OrchestrationContext,
    ) -> OrchestratedResult:
        """Assembles the final OrchestratedResult.

        Args:
            request_id: Originating request identifier.
            plan_id: Plan ID of the execution graph.
            graph: Graph detailing node statuses.
            ctx: Context tracking runtime timing and results.

        Returns:
            OrchestratedResult with combined payloads and metadata.
        """
        results = ctx.get_results()
        errors = ctx.get_errors()
        timings = ctx.get_timings()

        combined_results: Dict[str, Any] = {}
        citations: List[Citation] = []
        artifacts: List[Artifact] = []
        recommendations: List[Recommendation] = []
        executed_modules: List[str] = []

        confidence_sum = 0.0
        confidence_count = 0

        # Process each completed module result
        for mod, res in results.items():
            executed_modules.append(mod)

            # 1. Nest module results
            combined_results[mod] = res.get("structured_output", res)

            # 2. Extract confidence
            conf = res.get("confidence", 0.85)
            confidence_sum += conf
            confidence_count += 1

            # 3. Pull citations if present
            for c in res.get("citations", []):
                if isinstance(c, Citation):
                    citations.append(c)
                elif isinstance(c, dict):
                    citations.append(Citation(**c))

            # 4. Pull recommendations
            for r in res.get("recommendations", []):
                if isinstance(r, Recommendation):
                    recommendations.append(r)
                elif isinstance(r, dict):
                    recommendations.append(Recommendation(**r))

            # 5. Pull artifacts
            for a in res.get("artifacts", []):
                if isinstance(a, Artifact):
                    artifacts.append(a)
                elif isinstance(a, dict):
                    artifacts.append(Artifact(**a))

        # Executive summary synthesis
        n_ok = len(results)
        n_fail = len(errors)
        overall_conf = confidence_sum / confidence_count if confidence_count > 0 else 0.0

        summary_parts = [
            f"Orchestration complete. Successfully executed {n_ok} module(s) out of {n_ok + n_fail} planned.",
            f"Overall workflow confidence score is {overall_conf:.2f}.",
        ]
        if errors:
            summary_parts.append(f"Errors occurred in module(s): {', '.join(errors.keys())}.")

        status = (
            "completed" if n_fail == 0 and n_ok > 0
            else "partial" if n_ok > 0
            else "failed"
        )

        return OrchestratedResult(
            request_id=request_id,
            plan_id=plan_id,
            status=status,
            graph=graph,
            reasoning_summary=" ".join(summary_parts),
            combined_results=combined_results,
            citations=citations,
            artifacts=artifacts,
            recommendations=recommendations,
            modules_executed=executed_modules,
            execution_timeline=timings,
            confidence_score=round(overall_conf, 4),
            errors=errors,
        )
