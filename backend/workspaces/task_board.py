"""Task board manager tracking ticket items (pending, completed, failed, blocked)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import ProjectTask, TaskState


class TaskBoard:
    """Manages workspace ticket items and task state updates."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_tasks (
                task_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                assignee TEXT,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def add_task(
        self,
        project_id: str,
        title: str,
        assignee: Optional[str] = None,
    ) -> ProjectTask:
        """Adds a new task to the project board."""
        task = ProjectTask(
            task_id=f"tsk-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            title=title,
            status=TaskState.PENDING,
            assignee=assignee,
            created_at=datetime.utcnow().isoformat(),
        )
        self.save_task(task)
        return task

    def save_task(self, task: ProjectTask) -> None:
        """Saves task state to SQLite."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO project_tasks
                (task_id, project_id, title, status, assignee, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (task.task_id, task.project_id, task.title, task.status.value, task.assignee, task.created_at),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def update_task_status(self, task_id: str, status: TaskState) -> None:
        """Updates status of a task."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                "UPDATE project_tasks SET status = ? WHERE task_id = ?",
                (status.value, task_id),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def list_tasks(self, project_id: str) -> List[ProjectTask]:
        """Lists all tasks on the project board."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_tasks WHERE project_id = ?", (project_id,))
            rows = cursor.fetchall()
            tasks = []
            for r in rows:
                tasks.append(
                    ProjectTask(
                        task_id=r["task_id"],
                        project_id=r["project_id"],
                        title=r["title"],
                        status=TaskState(r["status"]),
                        assignee=r["assignee"],
                        created_at=r["created_at"],
                    )
                )
            return tasks
        except Exception:
            return []
        finally:
            conn.close()
