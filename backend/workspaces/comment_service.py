"""Comment service tracking project discussion commentary."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import Comment


class CommentService:
    """Manages project thread comment listings."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_comments (
                comment_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def add_comment(
        self,
        project_id: str,
        user_id: str,
        content: str,
    ) -> Comment:
        """Saves a comment post to database."""
        com = Comment(
            comment_id=f"com-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            user_id=user_id,
            content=content,
            created_at=datetime.utcnow().isoformat(),
        )
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO project_comments
                (comment_id, project_id, user_id, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (com.comment_id, com.project_id, com.user_id, com.content, com.created_at),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        return com

    def list_comments(self, project_id: str) -> List[Comment]:
        """Lists all commentary on a project workspace thread."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_comments WHERE project_id = ? ORDER BY created_at ASC", (project_id,))
            rows = cursor.fetchall()
            comments = []
            for r in rows:
                comments.append(
                    Comment(
                        comment_id=r["comment_id"],
                        project_id=r["project_id"],
                        user_id=r["user_id"],
                        content=r["content"],
                        created_at=r["created_at"],
                    )
                )
            return comments
        except Exception:
            return []
        finally:
            conn.close()
