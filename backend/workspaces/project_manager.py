"""Project manager handling workspace projects, cloning, templates, and archiving."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import Project


class ProjectManager:
    """Manages workspace projects, archiving states, and metadata cloning."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workspace_projects (
                project_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                tags TEXT NOT NULL,
                category TEXT NOT NULL,
                archived INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def create_project(
        self,
        workspace_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
    ) -> Project:
        """Creates and saves a new workspace project."""
        proj = Project(
            project_id=f"proj-{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            name=name,
            description=description,
            tags=tags or [],
            category=category,
            archived=False,
            created_at=datetime.utcnow().isoformat(),
        )
        self.save_project(proj)
        return proj

    def save_project(self, project: Project) -> None:
        """Saves a project state to SQLite."""
        import json
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO workspace_projects
                (project_id, workspace_id, name, description, tags, category, archived, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    project.project_id,
                    project.workspace_id,
                    project.name,
                    project.description,
                    json.dumps(project.tags),
                    project.category,
                    1 if project.archived else 0,
                    project.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_project(self, project_id: str) -> Optional[Project]:
        """Retrieves a project by ID."""
        import json
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspace_projects WHERE project_id = ?", (project_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return Project(
                project_id=r["project_id"],
                workspace_id=r["workspace_id"],
                name=r["name"],
                description=r["description"],
                tags=json.loads(r["tags"]),
                category=r["category"],
                archived=bool(r["archived"]),
                created_at=r["created_at"],
            )
        except Exception:
            return None
        finally:
            conn.close()

    def list_projects(self, workspace_id: str) -> List[Project]:
        """Lists active projects in a workspace."""
        import json
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspace_projects WHERE workspace_id = ? AND archived = 0", (workspace_id,))
            rows = cursor.fetchall()
            projects = []
            for r in rows:
                projects.append(
                    Project(
                        project_id=r["project_id"],
                        workspace_id=r["workspace_id"],
                        name=r["name"],
                        description=r["description"],
                        tags=json.loads(r["tags"]),
                        category=r["category"],
                        archived=bool(r["archived"]),
                        created_at=r["created_at"],
                    )
                )
            return projects
        except Exception:
            return []
        finally:
            conn.close()

    def archive_project(self, project_id: str) -> None:
        """Archives a project (marks archived = 1)."""
        proj = self.get_project(project_id)
        if proj:
            proj.archived = True
            self.save_project(proj)

    def clone_project(self, project_id: str, new_name: str) -> Optional[Project]:
        """Clones project metadata into a new project."""
        src = self.get_project(project_id)
        if src:
            return self.create_project(
                workspace_id=src.workspace_id,
                name=new_name,
                description=src.description,
                tags=src.tags,
                category=src.category,
            )
        return None
