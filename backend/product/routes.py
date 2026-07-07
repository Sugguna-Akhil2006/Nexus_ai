"""FastAPI router for the Nexus AI Product Experience Layer.

Provides REST endpoints for export, history management, background job
lifecycle, pipeline metrics, and developer console data. All endpoints
call product-layer services as black boxes and do not touch intelligence
modules or the runtime.

Endpoints
---------
POST   /product/export                      → ExportService
POST   /product/export/bundle               → ExportService.export_bundle
GET    /product/history                     → HistoryService.list
GET    /product/history/search              → HistoryService.search
GET    /product/history/{record_id}         → HistoryService.get
PATCH  /product/history/{record_id}/pin     → HistoryService.pin
PATCH  /product/history/{record_id}/favorite → HistoryService.favorite
DELETE /product/history/{record_id}         → HistoryService.delete
DELETE /product/history                     → HistoryService.bulk_delete
GET    /product/jobs                        → ProgressTracker.list_jobs
GET    /product/jobs/{job_id}               → ProgressTracker.get_job
POST   /product/jobs/{job_id}/cancel        → ProgressTracker.cancel_job
POST   /product/jobs/{job_id}/retry         → ProgressTracker.retry_job
GET    /product/jobs/summary                → ProgressTracker.summary
GET    /product/metrics/pipeline/{pipeline} → MetricsService.get_pipeline_metrics
GET    /product/metrics/snapshot            → MetricsService.get_performance_snapshot
GET    /product/console/timeline            → DeveloperConsoleAdapter.get_timeline
GET    /product/console/stages              → DeveloperConsoleAdapter.get_pipeline_stages
GET    /product/console/agents              → DeveloperConsoleAdapter.get_agent_status
GET    /product/console/metrics             → DeveloperConsoleAdapter.get_metrics_snapshot
GET    /product/cache/stats                 → CacheService.stats
DELETE /product/cache/{namespace}           → CacheService.invalidate_namespace
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, Query, Response
from pydantic import BaseModel, Field

from backend.product.cache_service import CacheService, _VALID_NAMESPACES
from backend.product.export_service import ExportService, ExportRequest
from backend.product.history_service import HistoryService
from backend.product.progress_tracker import ProgressTracker, JobStatus
from backend.product.metrics_service import MetricsService
from backend.product.serialization import ProductResponse, PaginatedResponse, paginate
from backend.product.frontend_adapter import DeveloperConsoleAdapter


router = APIRouter(prefix="/product", tags=["Product Experience Layer"])

# Singletons
_cache = CacheService()
_history = HistoryService()
_tracker = ProgressTracker()
_metrics = MetricsService()
_export_svc = ExportService()
_console_adapter = DeveloperConsoleAdapter()


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class ExportPayload(BaseModel):
    """Request body for single-format export."""

    report_id: str
    report_type: str = "resume"   # resume | github | document
    workspace_id: str = "default-ws"
    format: str = "json"          # json | html | markdown | pdf
    include_metadata: bool = True


class BundleExportPayload(BaseModel):
    """Request body for multi-format bundle export."""

    report_id: str
    report_type: str = "resume"
    workspace_id: str = "default-ws"
    formats: List[str] = Field(default_factory=lambda: ["json", "html", "markdown", "pdf"])


class BulkDeletePayload(BaseModel):
    """Request body for bulk history deletion."""

    record_ids: List[str]


class TimelinePayload(BaseModel):
    """Request body for timeline widget."""

    workflow_trace: List[Dict[str, Any]] = Field(default_factory=list)


class StagesPayload(BaseModel):
    """Request body for pipeline stages widget."""

    stage_timings: Dict[str, Any] = Field(default_factory=dict)


class AgentStatusPayload(BaseModel):
    """Request body for agent status widget."""

    agent_states: Dict[str, Any] = Field(default_factory=dict)


class EventStreamPayload(BaseModel):
    """Request body for event stream widget."""

    events: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Export Endpoints
# ---------------------------------------------------------------------------


def _load_report(report_id: str, report_type: str, workspace_id: str) -> Any:
    """Loads a report from cache or domain history services.

    Args:
        report_id: Report identifier.
        report_type: Domain type ('resume', 'github', 'document').
        workspace_id: Workspace identifier.

    Returns:
        Pydantic report object.

    Raises:
        HTTPException: 404 if the report is not found.
    """
    from backend.product.cache_service import NAMESPACE_REPORTS
    cached = _cache.get(NAMESPACE_REPORTS, report_id)
    if cached:
        # Reconstruct Pydantic model from cached dict
        if report_type == "resume":
            from backend.intelligence.resume.product import ProductResumeReport
            return ProductResumeReport.model_validate(cached)
        if report_type == "github":
            from backend.intelligence.github.models import GitHubIntelligenceReport
            return GitHubIntelligenceReport.model_validate(cached)
        if report_type == "document":
            from backend.intelligence.document.models import DocumentKnowledgeReport
            return DocumentKnowledgeReport.model_validate(cached)

    # Fall back to domain history services
    if report_type == "github":
        from backend.intelligence.github.history import GitHubHistoryManager
        report = GitHubHistoryManager().get_report(report_id)
        if report:
            return report

    raise HTTPException(
        status_code=404,
        detail=f"Report '{report_id}' not found in cache or history for type '{report_type}'.",
    )


@router.post("/export", summary="Export a report in a single format")
def export_report(payload: ExportPayload) -> Response:
    """Exports an intelligence report to the specified format.

    Downloads immediately as an attachment.
    """
    try:
        report = _load_report(payload.report_id, payload.report_type, payload.workspace_id)
        result = _export_svc.export(
            report,
            ExportRequest(
                format=payload.format,  # type: ignore[arg-type]
                include_metadata=payload.include_metadata,
            ),
        )
        return Response(
            content=result.content,
            media_type=result.media_type,
            headers={"Content-Disposition": f"attachment; filename={result.filename}"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/export/bundle", summary="Export a report as a ZIP bundle of all formats")
def export_bundle(payload: BundleExportPayload) -> Response:
    """Packages an intelligence report in multiple formats into a ZIP archive."""
    try:
        report = _load_report(payload.report_id, payload.report_type, payload.workspace_id)
        result = _export_svc.export_bundle(report, formats=payload.formats)
        return Response(
            content=result.content,
            media_type=result.media_type,
            headers={"Content-Disposition": f"attachment; filename={result.filename}"},
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# History Endpoints
# ---------------------------------------------------------------------------


@router.get("/history", summary="List analysis history for a workspace")
def list_history(
    workspace_id: str = Query(...),
    report_type: Optional[str] = Query(None),
    pinned_only: bool = Query(False),
    favorites_only: bool = Query(False),
    sort_by: str = Query("created_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Dict[str, Any]:
    """Lists history records with optional filtering, sorting, and pagination."""
    records = _history.list(
        workspace_id=workspace_id,
        report_type=report_type,
        pinned_only=pinned_only,
        favorites_only=favorites_only,
        sort_by=sort_by,
        sort_desc=sort_desc,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return {
        "success": True,
        "items": [r.model_dump() for r in records],
        "page": page,
        "page_size": page_size,
        "total": len(records),
    }


@router.get("/history/search", summary="Full-text search across history records")
def search_history(
    workspace_id: str = Query(...),
    q: str = Query(..., min_length=1),
    report_type: Optional[str] = Query(None),
    limit: int = Query(30, ge=1, le=100),
) -> Dict[str, Any]:
    """Searches history records by title, summary, and tags."""
    records = _history.search(
        workspace_id=workspace_id,
        query=q,
        report_type=report_type,
        limit=limit,
    )
    return {
        "success": True,
        "items": [r.model_dump() for r in records],
        "query": q,
        "total": len(records),
    }


@router.get("/history/{record_id}", summary="Get a single history record")
def get_history_record(record_id: str) -> Dict[str, Any]:
    """Retrieves a single analysis history record by ID."""
    record = _history.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"History record '{record_id}' not found.")
    return {"success": True, "data": record.model_dump()}


@router.patch("/history/{record_id}/pin", summary="Toggle pin state of a history record")
def pin_record(record_id: str, pinned: bool = Query(True)) -> Dict[str, Any]:
    """Pins or unpins a history record."""
    success = _history.pin(record_id, pinned=pinned)
    if not success:
        raise HTTPException(status_code=404, detail=f"History record '{record_id}' not found.")
    return {"success": True, "record_id": record_id, "is_pinned": pinned}


@router.patch("/history/{record_id}/favorite", summary="Toggle favorite state of a history record")
def favorite_record(record_id: str, favorited: bool = Query(True)) -> Dict[str, Any]:
    """Marks or unmarks a history record as a favorite."""
    success = _history.favorite(record_id, favorited=favorited)
    if not success:
        raise HTTPException(status_code=404, detail=f"History record '{record_id}' not found.")
    return {"success": True, "record_id": record_id, "is_favorite": favorited}


@router.delete("/history/{record_id}", summary="Delete a history record")
def delete_record(record_id: str) -> Dict[str, Any]:
    """Deletes a single analysis history record."""
    success = _history.delete(record_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"History record '{record_id}' not found.")
    return {"success": True, "deleted": record_id}


@router.delete("/history", summary="Bulk delete history records")
def bulk_delete_records(payload: BulkDeletePayload) -> Dict[str, Any]:
    """Deletes multiple history records by ID."""
    deleted = _history.bulk_delete(payload.record_ids)
    return {"success": True, "deleted_count": deleted}


# ---------------------------------------------------------------------------
# Background Job Endpoints
# ---------------------------------------------------------------------------


@router.get("/jobs/summary", summary="Get background job status summary")
def jobs_summary() -> Dict[str, Any]:
    """Returns count of jobs per status."""
    return {"success": True, "summary": _tracker.summary()}


@router.get("/jobs", summary="List background jobs")
def list_jobs(
    status: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Dict[str, Any]:
    """Lists tracked background jobs with optional status/type filtering."""
    js = JobStatus(status) if status else None
    jobs = _tracker.list_jobs(status=js, job_type=job_type, limit=limit)
    return {
        "success": True,
        "jobs": [j.model_dump() for j in jobs],
        "total": len(jobs),
    }


@router.get("/jobs/{job_id}", summary="Get a single background job")
def get_job(job_id: str) -> Dict[str, Any]:
    """Retrieves a single tracked job by ID."""
    job = _tracker.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return {"success": True, "job": job.model_dump()}


@router.post("/jobs/{job_id}/cancel", summary="Cancel a background job")
def cancel_job(job_id: str) -> Dict[str, Any]:
    """Cancels a queued or running background job."""
    success = _tracker.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{job_id}' could not be cancelled (not found or already terminal).",
        )
    return {"success": True, "job_id": job_id, "status": "cancelled"}


@router.post("/jobs/{job_id}/retry", summary="Retry a failed background job")
def retry_job(job_id: str) -> Dict[str, Any]:
    """Resets a failed job to QUEUED for re-execution."""
    success = _tracker.retry_job(job_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Job '{job_id}' could not be retried (not found, not failed, or max retries exceeded).",
        )
    return {"success": True, "job_id": job_id, "status": "queued"}


# ---------------------------------------------------------------------------
# Metrics Endpoints
# ---------------------------------------------------------------------------


@router.get("/metrics/snapshot", summary="Get global performance snapshot")
def get_performance_snapshot() -> Dict[str, Any]:
    """Returns a global performance snapshot across all tracked pipelines."""
    snapshot = _metrics.get_performance_snapshot()
    return {"success": True, "data": snapshot.model_dump()}


@router.get("/metrics/pipeline/{pipeline}", summary="Get metrics for a specific pipeline")
def get_pipeline_metrics(pipeline: str) -> Dict[str, Any]:
    """Returns aggregated metrics for a named pipeline."""
    metrics = _metrics.get_pipeline_metrics(pipeline)
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"No metrics found for pipeline '{pipeline}'.",
        )
    return {"success": True, "data": metrics.model_dump()}


@router.get("/metrics/pipelines", summary="List all tracked pipeline names")
def list_pipelines() -> Dict[str, Any]:
    """Returns the names of all pipelines with recorded executions."""
    return {"success": True, "pipelines": _metrics.list_pipelines()}


# ---------------------------------------------------------------------------
# Developer Console Endpoints
# ---------------------------------------------------------------------------


@router.post("/console/timeline", summary="Build execution timeline widget data")
def get_timeline(payload: TimelinePayload) -> Dict[str, Any]:
    """Converts a workflow trace into a normalised execution timeline."""
    return {"success": True, "data": _console_adapter.get_timeline(payload.workflow_trace)}


@router.post("/console/stages", summary="Build pipeline stage card data")
def get_stages(payload: StagesPayload) -> Dict[str, Any]:
    """Converts stage timings into pipeline stage card data."""
    return {"success": True, "data": _console_adapter.get_pipeline_stages(payload.stage_timings)}


@router.post("/console/agents", summary="Build agent status map data")
def get_agents(payload: AgentStatusPayload) -> Dict[str, Any]:
    """Builds a live agent status map for the developer console."""
    return {"success": True, "data": _console_adapter.get_agent_status(payload.agent_states)}


@router.get("/console/metrics", summary="Get developer console metrics snapshot")
def get_console_metrics(
    pipeline: Optional[str] = Query(None, description="Optional pipeline name filter"),
) -> Dict[str, Any]:
    """Returns a metrics snapshot formatted for the developer console."""
    return {"success": True, "data": _console_adapter.get_metrics_snapshot(pipeline)}


@router.post("/console/events", summary="Build event timeline widget data")
def get_events(payload: EventStreamPayload) -> Dict[str, Any]:
    """Converts raw event records into a chronological event stream."""
    return {"success": True, "data": _console_adapter.get_event_stream(payload.events)}


# ---------------------------------------------------------------------------
# Cache Management Endpoints
# ---------------------------------------------------------------------------


@router.get("/cache/stats", summary="Get cache hit/miss statistics")
def get_cache_stats() -> Dict[str, Any]:
    """Returns global cache statistics and per-namespace entry counts."""
    return {"success": True, "stats": _cache.stats()}


@router.delete("/cache/{namespace}", summary="Invalidate all entries in a cache namespace")
def invalidate_namespace(namespace: str) -> Dict[str, Any]:
    """Clears all entries in the specified cache namespace."""
    if namespace not in _VALID_NAMESPACES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid namespace '{namespace}'. Valid: {sorted(_VALID_NAMESPACES)}",
        )
    count = _cache.invalidate_namespace(namespace)
    return {"success": True, "namespace": namespace, "cleared_entries": count}


@router.get("/health", summary="Product layer health check")
def health() -> Dict[str, Any]:
    """Returns health status for all product-layer services."""
    return {
        "success": True,
        "status": "healthy",
        "services": {
            "cache": "ok",
            "history": "ok",
            "progress_tracker": "ok",
            "metrics": "ok",
            "export": "ok",
        },
    }
