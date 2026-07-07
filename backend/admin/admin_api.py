"""FastAPI REST routes for Enterprise Administration and System Monitoring."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query, Response

from backend.product.serialization import ProductResponse
from backend.admin.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Enterprise Administration"])

# Singleton orchestrator
_admin_svc = AdminService()


@router.get("/health", summary="Get system health checks")
def get_health() -> ProductResponse[Dict[str, Any]]:
    """Performs deep health check across database, WebSockets, and API gateways."""
    try:
        report = _admin_svc.get_health_report()
        return ProductResponse.ok(data=report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system", summary="Get system resource usage statistics")
def get_system() -> ProductResponse[Dict[str, Any]]:
    """Retrieves CPU, Memory, Disk, Cache, and task queue statistics."""
    try:
        stats = _admin_svc.get_system_report()
        return ProductResponse.ok(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", summary="Get analytics performance dashboard")
def get_metrics() -> ProductResponse[Dict[str, Any]]:
    """Aggregates execution durations, pipeline success rates, and module usage analytics."""
    try:
        metrics = _admin_svc.get_metrics_dashboard()
        return ProductResponse.ok(data=metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users", summary="Get enterprise users usage stats")
def get_users() -> ProductResponse[Dict[str, Any]]:
    """Compiles lists of active users, their workspace allocations, and storage indexes."""
    try:
        users = _admin_svc.get_users_list()
        return ProductResponse.ok(data=users)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit", summary="Get audit logs stream")
def get_audit(
    category: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> ProductResponse[List[Dict[str, Any]]]:
    """Retrieves chronological security compliance logs from audit tables."""
    try:
        logs = _admin_svc.audit.list_logs(category, user_id, limit, offset)
        return ProductResponse.ok(data=logs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications", summary="Get notifications timeline")
def get_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100)
) -> ProductResponse[List[Dict[str, Any]]]:
    """Lists current system warnings, alerts, and report completion flags."""
    try:
        notifs = _admin_svc.notifications.list_notifications(unread_only, limit)
        return ProductResponse.ok(data=notifs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/{id}/read", summary="Mark single notification as read")
def mark_read(id: str) -> ProductResponse[bool]:
    """Sets notification read status flag."""
    success = _admin_svc.notifications.mark_as_read(id)
    return ProductResponse.ok(data=success)


@router.post("/notifications/read-all", summary="Mark all notifications as read")
def mark_all_read() -> ProductResponse[int]:
    """Sets read status to true for all active warning notifications."""
    count = _admin_svc.notifications.mark_all_read()
    return ProductResponse.ok(data=count)
