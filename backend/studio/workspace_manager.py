"""Workspace Manager retrieving isolation context metadata for the studio."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from backend.agents.workspace import WorkspaceRegistry
from backend.api.sqlite_mock import DBStorage
from backend.studio.models import WorkspaceInfo


class WorkspaceManager:
    """Manages workspace inspection and stats retrieval for Nexus Studio."""

    def __init__(self) -> None:
        self.registry = WorkspaceRegistry()
        self._db = DBStorage()

    def get_workspace_info(self, workspace_id: str) -> Optional[WorkspaceInfo]:
        """Resolves workspace metadata and compiles info card."""
        providers = self.registry.list_providers()
        if not providers:
            return None

        provider = self.registry.get_provider(providers[0])
        try:
            ws = provider.get_workspace(workspace_id)
            members = provider.get_members(workspace_id)
        except Exception:
            return None

        if not ws:
            return None

        # Fetch active job count from sqlite
        active_jobs = 0
        conn = self._db._get_connection()
        try:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM public_jobs WHERE workspace_id = ? AND status IN ('pending', 'running')",
                (workspace_id,)
            ).fetchone()
            if row:
                active_jobs = row["count"]
        except Exception:
            pass
        finally:
            conn.close()

        return WorkspaceInfo(
            workspace_id=ws.workspace_id,
            name=ws.name,
            created_at=ws.created_at or datetime.utcnow().isoformat(),
            member_count=len(members),
            active_jobs_count=active_jobs
        )
