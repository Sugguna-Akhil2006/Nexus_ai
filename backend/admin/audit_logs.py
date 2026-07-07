"""Manages centralized relational Audit logging for security compliance and user actions."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage


class AuditLogsManager:
    """Thread-safe SQL compliance logger recording system-wide events and changes."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._init_db()

    def _init_db(self) -> None:
        """Ensures audit table exists."""
        conn = self._db._get_connection()
        try:
            with self._db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT NOT NULL,
                    category TEXT NOT NULL, -- auth | analysis | export | workspace_change | api_call | system_event
                    timestamp TEXT NOT NULL,
                    ip_address TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def log_action(self, user_id: str, action: str, details: str, category: str,
                   ip_address: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Appends a new immutable log record to the audit database."""
        log_id = f"aud-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._db._get_connection()
        try:
            with self._db._lock:
                conn.execute(
                    """
                    INSERT INTO audit_logs (log_id, user_id, action, details, category, timestamp, ip_address, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (log_id, user_id, action, details, category, now, ip_address, json.dumps(metadata or {}))
                )
                conn.commit()
        finally:
            conn.close()
        return log_id

    def list_logs(self, category: Optional[str] = None, user_id: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Queries and returns list of chronological audit rows."""
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            conditions = []
            params = []
            if category:
                conditions.append("category = ?")
                params.append(category)
            if user_id:
                conditions.append("user_id = ?")
                params.append(user_id)

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            sql = f"SELECT * FROM audit_logs {where_clause} ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
