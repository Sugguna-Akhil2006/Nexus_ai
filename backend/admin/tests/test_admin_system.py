"""Tests for enterprise administration package."""

import pytest
from backend.admin.admin_service import AdminService


@pytest.fixture(autouse=True)
def clean_db():
    """Wipes test notifications and audit logs."""
    from backend.api.sqlite_mock import DBStorage
    db = DBStorage()
    conn = db._get_connection()
    try:
        with db._lock:
            conn.execute("DELETE FROM system_notifications")
            conn.execute("DELETE FROM audit_logs")
            conn.commit()
    finally:
        conn.close()
    yield


def test_system_monitor():
    svc = AdminService()
    report = svc.get_system_report()
    
    assert "cpu_usage_pct" in report
    assert "memory_usage_mb" in report
    assert "disk_usage_pct" in report
    assert "queue_length" in report


def test_health_monitor():
    svc = AdminService()
    report = svc.get_health_report()
    
    assert report["status"] in ("healthy", "degraded")
    assert "database" in report["services"]
    assert "websocket" in report["services"]
    assert "api_gateway" in report["services"]


def test_audit_logs():
    svc = AdminService()
    log_id = svc.audit.log_action("admin", "test_action", "details", "system_event")
    
    assert log_id.startswith("aud-")
    logs = svc.audit.list_logs(category="system_event")
    assert len(logs) == 1
    assert logs[0]["action"] == "test_action"


def test_notifications():
    svc = AdminService()
    notif_id = svc.notifications.add_notification("Test Alert", "Message", "warning")
    
    assert notif_id.startswith("not-")
    notifs = svc.notifications.list_notifications()
    assert len(notifs) == 1
    assert notifs[0]["level"] == "warning"
    
    success = svc.notifications.mark_as_read(notif_id)
    assert success is True
    
    unread = svc.notifications.list_notifications(unread_only=True)
    assert len(unread) == 0


def test_usage_statistics():
    svc = AdminService()
    stats = svc.usage.get_usage_statistics()
    
    assert "total_users" in stats
    assert "total_workspaces" in stats
    assert "total_documents" in stats
