"""Manages live alert streams, pipelining status warnings, and analysis reports finished banners."""

import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage


class NotificationCenter:
    """Singleton alerting dispatcher caching system warnings, alerts, and report completion nodes."""

    _instance: Optional["NotificationCenter"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "NotificationCenter":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._db = DBStorage()
                instance._init_db()
                instance._lock = threading.RLock()
                cls._instance = instance
        return cls._instance

    def _init_db(self) -> None:
        """Initializes notifications table."""
        conn = self._db._get_connection()
        try:
            with self._db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS system_notifications (
                    notification_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    level TEXT NOT NULL, -- info | warning | alert | success
                    is_read INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def add_notification(self, title: str, message: str, level: str = "info", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Creates and stores a new system warning or banner alert."""
        notif_id = f"not-{str(uuid.uuid4())[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._db._get_connection()
        try:
            with self._lock:
                conn.execute(
                    """
                    INSERT INTO system_notifications (notification_id, title, message, level, is_read, created_at, metadata)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    """,
                    (notif_id, title, message, level, now, json.dumps(metadata or {}))
                )
                conn.commit()
        finally:
            conn.close()
        return notif_id

    def list_notifications(self, unread_only: bool = False, limit: int = 50) -> List[Dict[str, Any]]:
        """Queries notifications sorted by date."""
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            if unread_only:
                cursor.execute(
                    "SELECT * FROM system_notifications WHERE is_read = 0 ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            else:
                cursor.execute(
                    "SELECT * FROM system_notifications ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def mark_as_read(self, notification_id: str) -> bool:
        """Sets is_read state to true on alert row."""
        conn = self._db._get_connection()
        try:
            with self._lock:
                cursor = conn.execute(
                    "UPDATE system_notifications SET is_read = 1 WHERE notification_id = ?",
                    (notification_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        finally:
            conn.close()

    def mark_all_read(self) -> int:
        """Sets is_read = 1 on all alerts."""
        conn = self._db._get_connection()
        try:
            with self._lock:
                cursor = conn.execute("UPDATE system_notifications SET is_read = 1 WHERE is_read = 0")
                conn.commit()
                return cursor.rowcount
        finally:
            conn.close()
import threading  # Required for threading Lock in __new__
