"""Page-level frontend adapters for the Product Experience Layer.

Each adapter transforms raw AI intelligence API responses into clean,
frontend-ready payloads optimised for the specific product page's UI needs.
Adapters call existing intelligence APIs as black-box services and apply
product-layer transformations (serialization, history recording, caching).

Adapters
--------
- ResumePageAdapter        : Resume upload, analysis, history, export.
- GitHubPageAdapter        : Repository analysis, report fetch, dashboard stats.
- DocumentPageAdapter      : Document upload, analysis, querying, citations.
- ResearchPageAdapter      : Semantic search and citation retrieval.
- DeveloperConsoleAdapter  : Timeline, pipeline, agent status, metrics views.

All adapters are stateless (no mutable instance state) and safe for
concurrent use. They do not modify any intelligence module internals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.product.cache_service import CacheService, NAMESPACE_REPORTS, NAMESPACE_HISTORY, NAMESPACE_DASHBOARD, NAMESPACE_METRICS
from backend.product.history_service import HistoryService
from backend.product.export_service import ExportService, ExportRequest
from backend.product.serialization import serialize_report, paginate
from backend.product.developer_console import (
    ExecutionTimeline,
    PipelineStageWidget,
    AgentStatusWidget,
    PerformanceMetricsWidget,
    EventTimelineWidget,
)
from backend.product.metrics_service import MetricsService


# ---------------------------------------------------------------------------
# Resume Page Adapter
# ---------------------------------------------------------------------------


class ResumePageAdapter:
    """Frontend adapter for the Resume Intelligence product page.

    Wraps the resume analysis API, history service, and cache layer to
    provide clean, frontend-ready payloads for the Resume Analyzer page.
    """

    def __init__(self) -> None:
        self._cache = CacheService()
        self._history = HistoryService()
        self._export = ExportService()

    def format_analysis_result(
        self,
        report: Any,
        workspace_id: str,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Formats a ProductResumeReport into a frontend-ready payload.

        Saves the report to history and caches it for quick retrieval.

        Args:
            report: ProductResumeReport from the intelligence service.
            workspace_id: Owning workspace identifier.
            save_history: Whether to persist the report in history.

        Returns:
            Frontend-ready dict with report data and UI metadata.
        """
        report_dict = serialize_report(report)
        report_id = report_dict.get("report_id", "")

        # Cache the report
        self._cache.set(NAMESPACE_REPORTS, report_id, report_dict)

        # Persist to history
        if save_history:
            self._history.save_report(report, report_type="resume", workspace_id=workspace_id)

        return {
            "report_id": report_id,
            "ats_score": report_dict.get("ats_score", 0.0),
            "career_readiness": report_dict.get("career_readiness", ""),
            "executive_summary": report_dict.get("executive_summary", ""),
            "strengths": report_dict.get("strengths", []),
            "weaknesses": report_dict.get("weaknesses", []),
            "skill_analysis": report_dict.get("skill_analysis", {}),
            "missing_skills": report_dict.get("missing_skills", []),
            "improvement_roadmap": report_dict.get("improvement_roadmap", []),
            "action_plan": report_dict.get("action_plan", []),
            "job_match": report_dict.get("job_match"),
            "pipeline": report_dict.get("resume_pipeline", "Resume Intelligence"),
            "execution_id": report_dict.get("execution_id", ""),
            "module_timings": report_dict.get("module_timings", {}),
            "ui": {
                "score_color": _score_color(report_dict.get("ats_score", 0.0)),
                "export_formats": ["json", "html", "markdown", "pdf"],
            },
        }

    def get_history_page(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        favorites_only: bool = False,
    ) -> Dict[str, Any]:
        """Returns a paginated history list for the resume page.

        Args:
            workspace_id: Target workspace.
            page: Page number.
            page_size: Items per page.
            search: Optional search query.
            favorites_only: Filter to favorites only.

        Returns:
            Paginated history dict with UI metadata.
        """
        cache_key = f"resume_history_{workspace_id}_{page}_{search}"
        cached = self._cache.get(NAMESPACE_HISTORY, cache_key)
        if cached:
            return cached

        if search:
            records = self._history.search(workspace_id, search, report_type="resume")
        else:
            records = self._history.list(
                workspace_id,
                report_type="resume",
                favorites_only=favorites_only,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

        result = {
            "items": [r.model_dump() for r in records],
            "total": len(records),
            "page": page,
            "page_size": page_size,
        }
        self._cache.set(NAMESPACE_HISTORY, cache_key, result, ttl_seconds=60)
        return result

    def export_report(
        self,
        report: Any,
        fmt: str = "pdf",
    ) -> Dict[str, Any]:
        """Prepares an export result for the given format.

        Args:
            report: ProductResumeReport instance.
            fmt: Export format string.

        Returns:
            Dict with 'content', 'media_type', 'filename', 'size_bytes'.
        """
        result = self._export.export(report, ExportRequest(format=fmt))  # type: ignore[arg-type]
        return {
            "content": result.content,
            "media_type": result.media_type,
            "filename": result.filename,
            "size_bytes": result.size_bytes,
        }


# ---------------------------------------------------------------------------
# GitHub Page Adapter
# ---------------------------------------------------------------------------


class GitHubPageAdapter:
    """Frontend adapter for the GitHub Intelligence product page."""

    def __init__(self) -> None:
        self._cache = CacheService()
        self._history = HistoryService()
        self._export = ExportService()

    def format_analysis_result(
        self,
        report: Any,
        workspace_id: str,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Formats a GitHubIntelligenceReport into a frontend-ready payload.

        Args:
            report: GitHubIntelligenceReport from the intelligence service.
            workspace_id: Owning workspace identifier.
            save_history: Whether to persist the report in history.

        Returns:
            Frontend-ready dict with repository analysis data and UI metadata.
        """
        report_dict = serialize_report(report)
        report_id = report_dict.get("report_id", "")

        self._cache.set(NAMESPACE_REPORTS, report_id, report_dict)

        if save_history:
            self._history.save_report(report, report_type="github", workspace_id=workspace_id)

        quality = report_dict.get("engineering_quality", {})
        health = report_dict.get("repository_health", {})
        quality_score = quality.get("maintainability_score", 0.0)
        health_score = health.get("overall_health_score", 0.0)

        return {
            "report_id": report_id,
            "repository": report_dict.get("repository", ""),
            "executive_summary": report_dict.get("executive_summary", ""),
            "architecture_style": report_dict.get("architecture_style", ""),
            "technology_stack": report_dict.get("technology_stack", {}),
            "engineering_quality": quality,
            "repository_health": health,
            "documentation_quality": report_dict.get("documentation_quality", {}),
            "strengths": report_dict.get("strengths", []),
            "engineering_risks": report_dict.get("engineering_risks", []),
            "improvement_roadmap": report_dict.get("improvement_roadmap", []),
            "developer_skill_evidence": report_dict.get("developer_skill_evidence", []),
            "quality_score": quality_score,
            "health_score": health_score,
            "ui": {
                "quality_color": _score_color(quality_score),
                "health_color": _score_color(health_score),
                "export_formats": ["json", "html", "markdown", "pdf"],
                "show_dependency_graph": bool(report_dict.get("dependency_graph")),
            },
        }

    def get_dashboard_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Returns aggregated dashboard statistics for the GitHub page.

        Args:
            workspace_id: Target workspace.

        Returns:
            Dashboard stats dict with counts and recent reports.
        """
        cache_key = f"github_dashboard_{workspace_id}"
        cached = self._cache.get(NAMESPACE_DASHBOARD, cache_key)
        if cached:
            return cached

        counts = self._history.count(workspace_id)
        recent = self._history.list(workspace_id, report_type="github", limit=5)

        stats = {
            "total_analyses": counts.get("github", 0),
            "recent_reports": [r.model_dump() for r in recent],
            "workspace_id": workspace_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._cache.set(NAMESPACE_DASHBOARD, cache_key, stats, ttl_seconds=120)
        return stats

    def get_history_page(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Returns a paginated history list for the GitHub page.

        Args:
            workspace_id: Target workspace.
            page: Page number.
            page_size: Items per page.
            search: Optional search query.

        Returns:
            Paginated history dict.
        """
        if search:
            records = self._history.search(workspace_id, search, report_type="github")
        else:
            records = self._history.list(
                workspace_id, report_type="github",
                limit=page_size, offset=(page - 1) * page_size,
            )
        return {
            "items": [r.model_dump() for r in records],
            "total": len(records),
            "page": page,
            "page_size": page_size,
        }


# ---------------------------------------------------------------------------
# Document Page Adapter
# ---------------------------------------------------------------------------


class DocumentPageAdapter:
    """Frontend adapter for the Document Intelligence product page."""

    def __init__(self) -> None:
        self._cache = CacheService()
        self._history = HistoryService()
        self._export = ExportService()

    def format_analysis_result(
        self,
        report: Any,
        workspace_id: str,
        save_history: bool = True,
    ) -> Dict[str, Any]:
        """Formats a DocumentKnowledgeReport into a frontend-ready payload.

        Args:
            report: DocumentKnowledgeReport from the intelligence service.
            workspace_id: Owning workspace identifier.
            save_history: Whether to persist the report in history.

        Returns:
            Frontend-ready dict with document analysis data and UI metadata.
        """
        report_dict = serialize_report(report)
        report_id = report_dict.get("report_id", "")

        self._cache.set(NAMESPACE_REPORTS, report_id, report_dict)

        if save_history:
            self._history.save_report(report, report_type="document", workspace_id=workspace_id)

        confidence = report_dict.get("confidence_scores", {})
        overall_score = confidence.get("overall_score", 0.0)

        return {
            "report_id": report_id,
            "workspace_id": workspace_id,
            "document_ids": report_dict.get("document_ids", []),
            "summary": report_dict.get("summary", {}),
            "entities": report_dict.get("entities", []),
            "topics": report_dict.get("topics", []),
            "relationships": report_dict.get("relationships", []),
            "knowledge_objects": report_dict.get("knowledge_objects", []),
            "citations": report_dict.get("citations", []),
            "confidence_scores": confidence,
            "overall_confidence": overall_score,
            "ui": {
                "confidence_color": _score_color(overall_score * 100),
                "export_formats": ["json", "html", "markdown"],
                "citation_count": len(report_dict.get("citations", [])),
                "entity_count": len(report_dict.get("entities", [])),
            },
        }

    def format_citations(
        self,
        citations: List[Any],
        highlight_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Formats a citation list for the citation viewer component.

        Args:
            citations: List of Citation objects or dicts.
            highlight_query: Optional query string for snippet highlighting.

        Returns:
            List of formatted citation dicts with highlight metadata.
        """
        result = []
        for idx, cit in enumerate(citations):
            cit_dict = cit if isinstance(cit, dict) else (
                cit.model_dump() if hasattr(cit, "model_dump") else {}
            )
            snippet = cit_dict.get("snippet", cit_dict.get("text", ""))
            result.append({
                "index": idx + 1,
                "citation_id": cit_dict.get("citation_id", f"cit-{idx}"),
                "document_id": cit_dict.get("document_id", ""),
                "chunk_id": cit_dict.get("chunk_id", ""),
                "snippet": snippet,
                "relevance_score": cit_dict.get("relevance_score", 0.0),
                "metadata": cit_dict.get("metadata", {}),
                "has_highlight": bool(highlight_query and highlight_query.lower() in snippet.lower()),
            })
        return result

    def get_history_page(
        self,
        workspace_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Returns a paginated history list for the document page.

        Args:
            workspace_id: Target workspace.
            page: Page number.
            page_size: Items per page.

        Returns:
            Paginated history dict.
        """
        records = self._history.list(
            workspace_id, report_type="document",
            limit=page_size, offset=(page - 1) * page_size,
        )
        return {
            "items": [r.model_dump() for r in records],
            "total": len(records),
            "page": page,
            "page_size": page_size,
        }


# ---------------------------------------------------------------------------
# Research Page Adapter
# ---------------------------------------------------------------------------


class ResearchPageAdapter:
    """Frontend adapter for the Research / RAG product page."""

    def __init__(self) -> None:
        self._cache = CacheService()

    def format_search_results(
        self,
        results: List[Any],
        query: str,
        total_time_ms: float = 0.0,
    ) -> Dict[str, Any]:
        """Formats semantic search results for the research page UI.

        Args:
            results: List of SearchResult objects or dicts.
            query: The original search query.
            total_time_ms: Total retrieval time in milliseconds.

        Returns:
            Frontend-ready dict with results and search metadata.
        """
        formatted = []
        for idx, res in enumerate(results):
            res_dict = res if isinstance(res, dict) else (
                res.model_dump() if hasattr(res, "model_dump") else {}
            )
            formatted.append({
                "rank": idx + 1,
                "result_id": res_dict.get("result_id", f"r-{idx}"),
                "document_id": res_dict.get("document_id", ""),
                "chunk_id": res_dict.get("chunk_id", ""),
                "snippet": res_dict.get("snippet", ""),
                "score": round(res_dict.get("score", 0.0), 4),
                "source": res_dict.get("source", ""),
                "metadata": res_dict.get("metadata", {}),
            })
        return {
            "query": query,
            "results": formatted,
            "result_count": len(formatted),
            "retrieval_time_ms": round(total_time_ms, 2),
            "has_results": bool(formatted),
        }

    def format_citations_for_display(
        self,
        chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Formats retrieved RAG chunks for the citation viewer.

        Args:
            chunks: List of chunk dicts from WebSocket metadata.

        Returns:
            List of citation display dicts.
        """
        return [
            {
                "index": chunk.get("chunk_number", idx + 1),
                "document": chunk.get("document_name", chunk.get("document_id", "")),
                "section": chunk.get("section_name", "General"),
                "snippet": chunk.get("snippet", ""),
                "score": chunk.get("similarity_score", 0.0),
                "included": chunk.get("included_in_prompt", True),
            }
            for idx, chunk in enumerate(chunks)
        ]


# ---------------------------------------------------------------------------
# Developer Console Adapter
# ---------------------------------------------------------------------------


class DeveloperConsoleAdapter:
    """Frontend adapter for the Developer Console page."""

    def __init__(self) -> None:
        self._cache = CacheService()
        self._metrics = MetricsService()

    def get_timeline(self, workflow_trace: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds an execution timeline payload from a workflow trace.

        Args:
            workflow_trace: List of trace step dicts.

        Returns:
            Dict with 'steps', 'total_steps', 'error_count'.
        """
        steps = ExecutionTimeline.build(workflow_trace)
        error_count = sum(1 for s in steps if s.get("has_error"))
        return {
            "steps": steps,
            "total_steps": len(steps),
            "error_count": error_count,
            "has_errors": error_count > 0,
        }

    def get_pipeline_stages(
        self,
        stage_timings: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Builds pipeline stage card data for the developer console.

        Args:
            stage_timings: Dict mapping stage name to timing value.

        Returns:
            Dict with 'stages' and 'total_stages'.
        """
        stages = PipelineStageWidget.build(stage_timings)
        return {
            "stages": stages,
            "total_stages": len(stages),
            "slowest_stage": stages[0]["stage"] if stages else None,
        }

    def get_agent_status(
        self,
        agent_states: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Builds a live agent status map for the developer console.

        Args:
            agent_states: Dict mapping agent name to state dict.

        Returns:
            Dict with 'agents', 'active_count', 'total_count'.
        """
        agents = AgentStatusWidget.build(agent_states)
        active_count = sum(1 for a in agents.values() if a.get("is_active"))
        return {
            "agents": agents,
            "active_count": active_count,
            "total_count": len(agents),
        }

    def get_metrics_snapshot(self, pipeline: Optional[str] = None) -> Dict[str, Any]:
        """Returns a performance metrics snapshot for the console.

        Args:
            pipeline: Optional pipeline name filter.

        Returns:
            Dict with KPI cards and raw metrics.
        """
        cache_key = f"metrics_{pipeline or 'global'}"
        cached = self._cache.get(NAMESPACE_METRICS, cache_key)
        if cached:
            return cached

        if pipeline:
            metrics = self._metrics.get_pipeline_metrics(pipeline)
        else:
            metrics = self._metrics.get_performance_snapshot()

        kpi_cards = PerformanceMetricsWidget.build(metrics) if metrics else []
        result = {
            "kpi_cards": kpi_cards,
            "raw_metrics": metrics.model_dump() if hasattr(metrics, "model_dump") else {},
            "pipeline": pipeline or "all",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._cache.set(NAMESPACE_METRICS, cache_key, result, ttl_seconds=30)
        return result

    def get_event_stream(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Builds a chronological event stream for the console.

        Args:
            events: List of event dicts with 'timestamp' and 'event' keys.

        Returns:
            Dict with 'events', 'total_events'.
        """
        stream = EventTimelineWidget.build(events)
        return {
            "events": stream,
            "total_events": len(stream),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _score_color(score: float) -> str:
    """Returns a CSS color string based on a 0–100 score."""
    if score >= 80:
        return "#22c55e"   # green
    if score >= 60:
        return "#eab308"   # yellow
    if score >= 40:
        return "#f97316"   # orange
    return "#ef4444"       # red
