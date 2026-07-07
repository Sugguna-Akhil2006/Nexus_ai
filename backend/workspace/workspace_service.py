"""Workspace Service coordinating DB interactions for metadata, pins, favorites, and settings."""

import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.workspace.workspace_models import WorkspaceDetail, WorkspaceSettings


class WorkspaceService:
    """Thread-safe service managing workspaces metadata, status flags, and settings."""

    _instance: Optional["WorkspaceService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "WorkspaceService":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._db = DBStorage()
                instance._init_tables()
                instance._lock = threading.RLock()
                cls._instance = instance
        return cls._instance

    def _init_tables(self) -> None:
        """Initializes tables for workspace settings, pins, favorites, and archived status."""
        conn = self._db._get_connection()
        try:
            with self._db._lock:
                # Add columns dynamically to workspaces table if missing, or create workspace_metadata
                conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_metadata (
                    workspace_id TEXT PRIMARY KEY,
                    is_pinned INTEGER NOT NULL DEFAULT 0,
                    is_favorite INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    industry TEXT NOT NULL DEFAULT 'Technology & SaaS',
                    deployment TEXT NOT NULL DEFAULT 'private',
                    description TEXT NOT NULL DEFAULT '',
                    custom_metadata TEXT NOT NULL DEFAULT '{}'
                )
                """)
                conn.execute("""
                CREATE TABLE IF NOT EXISTS workspace_activity (
                    activity_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def create_workspace(self, name: str, owner_id: str, settings: Optional[WorkspaceSettings] = None) -> WorkspaceDetail:
        """Creates a new workspace, settings, owner membership, and metadata."""
        workspace_id = f"ws-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc)
        sets = settings or WorkspaceSettings()

        # Write core workspace record to spaces table
        self._db.create_workspace(workspace_id, name, owner_id)

        conn = self._db._get_connection()
        try:
            with self._lock:
                conn.execute(
                    """
                    INSERT INTO workspace_metadata 
                    (workspace_id, is_pinned, is_favorite, updated_at, industry, deployment, description, custom_metadata)
                    VALUES (?, 0, 0, ?, ?, ?, ?, '{}')
                    """,
                    (workspace_id, now.isoformat(), sets.industry, sets.deployment, sets.description)
                )
                conn.commit()
        finally:
            conn.close()

        self.log_activity(workspace_id, owner_id, "workspace_change", f"Created workspace '{name}'")

        return WorkspaceDetail(
            workspace_id=workspace_id,
            name=name,
            owner_id=owner_id,
            status="active",
            created_at=now,
            updated_at=now,
            is_pinned=False,
            is_favorite=False,
            settings=sets,
            metadata={}
        )

    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceDetail]:
        """Retrieves complete workspace details."""
        conn = self._db._get_connection()
        try:
            # Query base table and meta table
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT w.name, w.owner_id, w.status, w.created_at,
                       m.is_pinned, m.is_favorite, m.updated_at, m.industry, m.deployment, m.description, m.custom_metadata
                FROM workspaces w
                LEFT JOIN workspace_metadata m ON w.workspace_id = m.workspace_id
                WHERE w.workspace_id = ?
                """,
                (workspace_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None

            settings = WorkspaceSettings(
                industry=row["industry"] or "Technology & SaaS",
                deployment=row["deployment"] or "private",
                description=row["description"] or ""
            )

            created_time = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
            updated_time = datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(timezone.utc)

            return WorkspaceDetail(
                workspace_id=workspace_id,
                name=row["name"],
                owner_id=row["owner_id"],
                status=row["status"] or "active",
                created_at=created_time,
                updated_at=updated_time,
                is_pinned=bool(row["is_pinned"]),
                is_favorite=bool(row["is_favorite"]),
                settings=settings,
                metadata=json.loads(row["custom_metadata"] or "{}")
            )
        finally:
            conn.close()

    def list_workspaces(self, user_id: str, include_archived: bool = True) -> List[WorkspaceDetail]:
        """Lists workspaces the user belongs to, decorated with settings and metadata."""
        conn = self._db._get_connection()
        workspaces = []
        try:
            cursor = conn.cursor()
            # Fetch workspaces where user is member
            query = """
                SELECT w.workspace_id, w.name, w.owner_id, w.status, w.created_at,
                       m.is_pinned, m.is_favorite, m.updated_at, m.industry, m.deployment, m.description, m.custom_metadata
                FROM workspaces w
                JOIN members mem ON w.workspace_id = mem.workspace_id
                LEFT JOIN workspace_metadata m ON w.workspace_id = m.workspace_id
                WHERE mem.user_id = ?
            """
            if not include_archived:
                query += " AND w.status = 'active'"
            
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            for r in rows:
                settings = WorkspaceSettings(
                    industry=r["industry"] or "Technology & SaaS",
                    deployment=r["deployment"] or "private",
                    description=r["description"] or ""
                )
                created_time = datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc)
                updated_time = datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else datetime.now(timezone.utc)

                workspaces.append(WorkspaceDetail(
                    workspace_id=r["workspace_id"],
                    name=r["name"],
                    owner_id=r["owner_id"],
                    status=r["status"] or "active",
                    created_at=created_time,
                    updated_at=updated_time,
                    is_pinned=bool(r["is_pinned"]),
                    is_favorite=bool(r["is_favorite"]),
                    settings=settings,
                    metadata=json.loads(r["custom_metadata"] or "{}")
                ))
        finally:
            conn.close()
        return workspaces

    def update_workspace(self, workspace_id: str, name: Optional[str] = None, status: Optional[str] = None,
                         is_pinned: Optional[bool] = None, is_favorite: Optional[bool] = None,
                         settings: Optional[WorkspaceSettings] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Updates workspace details, settings, and pins/favorites."""
        conn = self._db._get_connection()
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self._lock:
                # Update main table name or status if present
                if name or status:
                    update_fields = []
                    params = []
                    if name:
                        update_fields.append("name = ?")
                        params.append(name)
                    if status:
                        update_fields.append("status = ?")
                        params.append(status)
                    params.append(workspace_id)
                    conn.execute(f"UPDATE workspaces SET {', '.join(update_fields)} WHERE workspace_id = ?", params)

                # Ensure meta entry exists
                conn.execute("INSERT OR IGNORE INTO workspace_metadata (workspace_id, updated_at) VALUES (?, ?)", (workspace_id, now))

                # Update metadata table
                meta_fields = ["updated_at = ?"]
                meta_params = [now]
                if is_pinned is not None:
                    meta_fields.append("is_pinned = ?")
                    meta_params.append(int(is_pinned))
                if is_favorite is not None:
                    meta_fields.append("is_favorite = ?")
                    meta_params.append(int(is_favorite))
                if settings:
                    meta_fields.append("industry = ?")
                    meta_params.append(settings.industry)
                    meta_fields.append("deployment = ?")
                    meta_params.append(settings.deployment)
                    meta_fields.append("description = ?")
                    meta_params.append(settings.description)
                if metadata is not None:
                    meta_fields.append("custom_metadata = ?")
                    meta_params.append(json.dumps(metadata))

                meta_params.append(workspace_id)
                conn.execute(f"UPDATE workspace_metadata SET {', '.join(meta_fields)} WHERE workspace_id = ?", meta_params)
                conn.commit()
                
                self.log_activity(workspace_id, "admin", "workspace_change", f"Updated settings for workspace '{workspace_id}'")
                return True
        finally:
            conn.close()

    def log_activity(self, workspace_id: str, user_id: str, activity_type: str, description: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Appends a new event log to the activity timeline."""
        activity_id = f"act-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._db._get_connection()
        try:
            with self._lock:
                conn.execute(
                    """
                    INSERT INTO workspace_activity (activity_id, workspace_id, user_id, activity_type, description, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (activity_id, workspace_id, user_id, activity_type, description, now, json.dumps(metadata or {}))
                )
                conn.commit()
        finally:
            conn.close()
        return activity_id

    def get_activities(self, workspace_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves chronologically sorted activity records for a workspace."""
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workspace_activity WHERE workspace_id = ? ORDER BY timestamp DESC LIMIT ?",
                (workspace_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
