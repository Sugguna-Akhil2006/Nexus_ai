"""Tests for workspace management package."""

import pytest
from datetime import datetime, timezone
from backend.workspace.workspace_service import WorkspaceService
from backend.workspace.workspace_models import WorkspaceSettings, WorkspaceCreatePayload, WorkspaceUpdatePayload
from backend.workspace.workspace_dashboard import WorkspaceDashboardService
from backend.workspace.workspace_search import WorkspaceSearchService
from backend.workspace.workspace_export import WorkspaceExportService


@pytest.fixture(autouse=True)
def clean_db():
    """Wipes test workspaces from SQLite database."""
    svc = WorkspaceService()
    conn = svc._db._get_connection()
    try:
        with svc._db._lock:
            conn.execute("DELETE FROM workspaces WHERE workspace_id LIKE 'ws-test%'")
            conn.execute("DELETE FROM workspace_metadata WHERE workspace_id LIKE 'ws-test%'")
            conn.execute("DELETE FROM workspace_activity WHERE workspace_id LIKE 'ws-test%'")
            conn.commit()
    finally:
        conn.close()
    yield


def test_create_workspace():
    svc = WorkspaceService()
    settings = WorkspaceSettings(industry="Healthcare", deployment="cloud", description="Test Description")
    ws = svc.create_workspace("Test Health Space", "admin", settings)
    
    assert ws.workspace_id.startswith("ws-")
    assert ws.name == "Test Health Space"
    assert ws.settings.industry == "Healthcare"
    assert ws.settings.deployment == "cloud"


def test_get_workspace():
    svc = WorkspaceService()
    settings = WorkspaceSettings(industry="Legal & Compliance", deployment="private", description="Legal Dept")
    ws = svc.create_workspace("Legal space", "admin", settings)
    
    retrieved = svc.get_workspace(ws.workspace_id)
    assert retrieved is not None
    assert retrieved.name == "Legal space"
    assert retrieved.settings.description == "Legal Dept"


def test_update_workspace():
    svc = WorkspaceService()
    ws = svc.create_workspace("Initial Name", "admin")
    
    updated = svc.update_workspace(ws.workspace_id, name="Updated Name", is_pinned=True, is_favorite=True)
    assert updated is True
    
    retrieved = svc.get_workspace(ws.workspace_id)
    assert retrieved.name == "Updated Name"
    assert retrieved.is_pinned is True
    assert retrieved.is_favorite is True


def test_dashboard_aggregator():
    svc = WorkspaceService()
    ws = svc.create_workspace("Dashboard space", "admin")
    
    dashboard_svc = WorkspaceDashboardService()
    data = dashboard_svc.get_dashboard(ws.workspace_id)
    
    assert data.workspace.name == "Dashboard space"
    assert data.stats.total_documents == 0
    assert len(data.timeline) >= 1  # Workspace creation activity should be recorded


def test_search_service():
    svc = WorkspaceService()
    ws = svc.create_workspace("Search space", "admin")
    
    search_svc = WorkspaceSearchService()
    results = search_svc.search(ws.workspace_id, "nomatchquery")
    assert len(results) == 0


def test_export_service():
    svc = WorkspaceService()
    ws = svc.create_workspace("Export space", "admin")
    
    export_svc = WorkspaceExportService()
    zip_bytes = export_svc.export_workspace(ws.workspace_id)
    assert len(zip_bytes) > 100  # Should produce a valid zip file structure
