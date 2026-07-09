"""Artifact manager storing workspace reports, code, and diagrams."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.models import Artifact


class ArtifactManager:
    """Manages project documents, code links, and design diagram artifacts."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_artifacts (
                artifact_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def add_artifact(
        self,
        project_id: str,
        name: str,
        artifact_type: str,
        content: str,
    ) -> Artifact:
        """Stores a new artifact in the database."""
        art = Artifact(
            artifact_id=f"art-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            name=name,
            artifact_type=artifact_type,
            content=content,
            created_at=datetime.utcnow().isoformat(),
        )
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO project_artifacts
                (artifact_id, project_id, name, artifact_type, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (art.artifact_id, art.project_id, art.name, art.artifact_type, art.content, art.created_at),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        return art

    def list_artifacts(self, project_id: str) -> List[Artifact]:
        """Lists all artifacts associated with a project."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM project_artifacts WHERE project_id = ?", (project_id,))
            rows = cursor.fetchall()
            artifacts = []
            for r in rows:
                artifacts.append(
                    Artifact(
                        artifact_id=r["artifact_id"],
                        project_id=r["project_id"],
                        name=r["name"],
                        artifact_type=r["artifact_type"],
                        content=r["content"],
                        created_at=r["created_at"],
                    )
                )
            return artifacts
        except Exception:
            return []
        finally:
            conn.close()
