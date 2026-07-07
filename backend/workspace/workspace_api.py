"""FastAPI API routes implementing Workspace endpoints and switch/settings/dashboard controllers."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, Response

from backend.product.serialization import ProductResponse
from backend.workspace.workspace_models import (
    WorkspaceDetail,
    WorkspaceCreatePayload,
    WorkspaceUpdatePayload,
    WorkspaceDashboardData,
    SearchQueryPayload,
    SearchResultItem
)
from backend.workspace.workspace_service import WorkspaceService
from backend.workspace.workspace_history import WorkspaceHistoryService
from backend.workspace.workspace_search import WorkspaceSearchService
from backend.workspace.workspace_export import WorkspaceExportService
from backend.workspace.workspace_dashboard import WorkspaceDashboardService

router = APIRouter(prefix="/workspace", tags=["Workspace Management"])

# Singletons
_ws_svc = WorkspaceService()
_history_svc = WorkspaceHistoryService()
_search_svc = WorkspaceSearchService()
_export_svc = WorkspaceExportService()
_dashboard_svc = WorkspaceDashboardService()


@router.get("", summary="List workspaces for the user")
def list_workspaces(user_id: str = Query("admin"), include_archived: bool = Query(True)) -> ProductResponse[List[WorkspaceDetail]]:
    """Lists workspaces associated with the user, decorated with metadata."""
    try:
        spaces = _ws_svc.list_workspaces(user_id, include_archived)
        return ProductResponse.ok(data=spaces)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", summary="Create a new workspace")
def create_workspace(payload: WorkspaceCreatePayload) -> ProductResponse[WorkspaceDetail]:
    """Creates a new workspace namespace and owner associations."""
    try:
        ws = _ws_svc.create_workspace(payload.name, payload.owner_id, payload.settings)
        return ProductResponse.ok(data=ws)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}", summary="Get workspace details")
def get_workspace(id: str) -> ProductResponse[WorkspaceDetail]:
    """Retrieves full details of a specific workspace."""
    ws = _ws_svc.get_workspace(id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{id}' not found.")
    return ProductResponse.ok(data=ws)


@router.put("/{id}", summary="Update workspace properties or settings")
def update_workspace(id: str, payload: WorkspaceUpdatePayload) -> ProductResponse[bool]:
    """Updates workspace settings, flags (favorite, pin), and attributes."""
    ws = _ws_svc.get_workspace(id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{id}' not found.")
    
    success = _ws_svc.update_workspace(
        workspace_id=id,
        name=payload.name,
        status=payload.status,
        is_pinned=payload.is_pinned,
        is_favorite=payload.is_favorite,
        settings=payload.settings,
        metadata=payload.metadata
    )
    return ProductResponse.ok(data=success)


@router.delete("/{id}", summary="Archive or delete workspace")
def delete_workspace(id: str) -> ProductResponse[bool]:
    """Sets a workspace status to archived/deleted."""
    ws = _ws_svc.get_workspace(id)
    if not ws:
        raise HTTPException(status_code=404, detail=f"Workspace '{id}' not found.")
    
    success = _ws_svc.update_workspace(id, status="deleted")
    return ProductResponse.ok(data=success)


@router.get("/{id}/dashboard", summary="Retrieve Workspace Dashboard summary")
def get_workspace_dashboard(id: str) -> ProductResponse[WorkspaceDashboardData]:
    """Aggregates telemetry, statistics, and history timelines for the active workspace."""
    try:
        dashboard = _dashboard_svc.get_dashboard(id)
        return ProductResponse.ok(data=dashboard)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", summary="Get consolidated analysis history")
def get_history(
    workspace_id: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> ProductResponse[List[Dict[str, Any]]]:
    """Retrieves chronological analyses (Resume, GitHub, Doc) across the workspace."""
    try:
        history = _history_svc.get_consolidated_history(workspace_id, limit, offset)
        return ProductResponse.ok(data=history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", summary="Unified search within workspace")
def search_workspace(
    workspace_id: str = Query(...),
    q: str = Query(..., min_length=1),
    types: Optional[List[str]] = Query(None),
    limit: int = Query(20, ge=1, le=50)
) -> ProductResponse[List[SearchResultItem]]:
    """Performs global search matching documents, repos, and analysis reports."""
    try:
        results = _search_svc.search(workspace_id, q, types, limit)
        return ProductResponse.ok(data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/export", summary="Export workspace ZIP bundle")
def export_workspace(id: str, formats: Optional[List[str]] = Query(None)) -> Response:
    """Exports full workspace metadata and reports catalog into a downloadable ZIP bundle."""
    try:
        zip_bytes = _export_svc.export_workspace(id, formats)
        filename = f"workspace_{id}_export.zip"
        return Response(
            content=zip_bytes,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
