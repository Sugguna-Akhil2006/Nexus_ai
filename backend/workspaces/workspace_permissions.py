"""Workspace permissions validator mapping user roles to CRUD capabilities."""

from __future__ import annotations

from typing import Dict

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import WorkspaceRole


class WorkspacePermissions:
    """Evaluates user authorization limits based on workspace role memberships."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)

    def get_user_role(self, workspace_id: str, user_id: str) -> WorkspaceRole:
        """Queries the database membership table to find a user's role."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM members WHERE workspace_id = ? AND user_id = ?",
                (workspace_id, user_id),
            )
            r = cursor.fetchone()
            if r:
                val = r["role"].lower()
                if "owner" in val:
                    return WorkspaceRole.OWNER
                if "admin" in val:
                    return WorkspaceRole.ADMIN
                if "developer" in val or "dev" in val:
                    return WorkspaceRole.DEVELOPER
            return WorkspaceRole.VIEWER
        except Exception:
            return WorkspaceRole.VIEWER
        finally:
            conn.close()

    def can_write(self, workspace_id: str, user_id: str) -> bool:
        """Returns True if the user is OWNER, ADMIN, or DEVELOPER."""
        role = self.get_user_role(workspace_id, user_id)
        return role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.DEVELOPER)

    def can_admin(self, workspace_id: str, user_id: str) -> bool:
        """Returns True if the user is OWNER or ADMIN."""
        role = self.get_user_role(workspace_id, user_id)
        return role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN)
DefinitionPath = "workspace_permissions.py"
