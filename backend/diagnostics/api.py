"""FastAPI APIRouter routing diagnostics queries and exporting CSV/Markdown/JSON telemetry reports."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from backend.diagnostics.diagnostic_manager import DiagnosticManager
from backend.diagnostics.performance_dashboard import PerformanceDashboard
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/diagnostics", tags=["System Diagnostics"])

# Singleton manager
_manager = DiagnosticManager()


@router.get("/requests", summary="Get request logs and traces")
def get_requests(
    format: str = Query("json", regex="^(json|csv|markdown)$"),
    workspace_id: Optional[str] = Query(None),
) -> Any:
    """Retrieves RequestTraces filtered by workspace, formatted in JSON, CSV, or Markdown."""
    raw_traces = _manager.history.list_traces()

    # Filter by workspace if supplied
    if workspace_id:
        raw_traces = [t for t in raw_traces if t["workspace_id"] == workspace_id]

    if format == "csv":
        csv_content = _manager.history.export_csv(raw_traces)
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=requests_diagnostic.csv"})

    if format == "markdown":
        md_content = _manager.history.export_markdown(raw_traces)
        return Response(content=md_content, media_type="text/markdown")

    # Default JSON
    return ProductResponse.ok(data=raw_traces)


@router.get("/workflows", summary="Get active workflow tracker details")
def get_workflows() -> ProductResponse[Dict[str, Any]]:
    """Lists current state and variables of running workflows."""
    traces = _manager.history.list_traces()
    workflow_summaries = {}
    for t in traces:
        workflow_summaries[t["request_id"]] = {
            "workspace_id": t["workspace_id"],
            "status": t["status"],
            "duration_ms": t["duration_ms"],
            "modules_used": t["modules_used"],
            "timeline": t["timeline"],
        }
    return ProductResponse.ok(data=workflow_summaries)


@router.get("/providers", summary="Get AI provider latency and tokens")
def get_providers() -> ProductResponse[List[Any]]:
    """Returns aggregated call latency summaries and token usage across LLMs."""
    summaries = _manager.provider_tracker.list_summaries()
    return ProductResponse.ok(data=[s.model_dump() for s in summaries])


@router.get("/errors", summary="Get error records categorized")
def get_errors() -> ProductResponse[List[Dict[str, Any]]]:
    """Returns trace records containing failed execution steps."""
    traces = _manager.history.list_traces()
    error_list = []
    for t in traces:
        if t["errors"]:
            error_list.append({
                "request_id": t["request_id"],
                "workspace_id": t["workspace_id"],
                "errors": t["errors"],
                "created_at": t["created_at"],
            })
    return ProductResponse.ok(data=error_list)


@router.get("/performance", summary="Get CPU, memory, and latency snapshots")
def get_performance() -> ProductResponse[Dict[str, Any]]:
    """Assembles a performance snapshot detailing memory usage, CPU time, and averages."""
    traces = _manager.history.list_traces()
    stats = PerformanceDashboard.get_dashboard_data(traces)
    return ProductResponse.ok(data=stats)
