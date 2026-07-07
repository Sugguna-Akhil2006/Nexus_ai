"""Activity feed manager logging user activities and agent events."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import ActivityRecord


class ActivityFeed:
    """Manages workspace events logging and audit history feeds."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_activities (
                activity_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def log_activity(
        self,
        project_id: str,
        event_type: str,
        user_id: str,
        description: str,
    ) -> ActivityRecord:
        """Saves a new activity record to SQLite."""
        act = ActivityRecord(
            activity_id=f"act-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            event_type=event_type,
            user_id=user_id,
            description=description,
            created_at=datetime.utcnow().isoformat(),
        )
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO workspace_activities
                (activity_id, project_id, event_type, user_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (act.activity_id, act.project_id, act.event_type, act.user_id, act.description, act.created_at),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        return act

    def get_feed(self, project_id: str) -> List[ActivityRecord]:
        """Lists chronological history events of a project."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspace_activities WHERE project_id = ? ORDER BY created_at DESC", (project_id,))
            rows = cursor.fetchall()
            feed = []
            for r in rows:
                feed.append(
                    ActivityRecord(
                        activity_id=r["activity_id"],
                        project_id=r["project_id"],
                        event_type=r["event_type"],
                        user_id=r["user_id"],
                        description=r["description"],
                        created_at=r["created_at"],
                    )
                )
            return feed
        except Exception:
            return []
        finally:
            conn.close()
