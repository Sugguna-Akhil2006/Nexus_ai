"""Template versioning manager handling versions snapshots and rollbacks."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workflow_library.models import TemplateVersion, WorkflowTemplate


class TemplateVersioning:
    """Manages version historical records and rollbacks in SQLite."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS template_versions (
                version TEXT NOT NULL,
                template_id TEXT NOT NULL,
                steps TEXT NOT NULL,
                changelog TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY (version, template_id)
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def save_version_snapshot(
        self,
        template: WorkflowTemplate,
        changelog: Optional[str] = None,
    ) -> TemplateVersion:
        """Stores a snapshot representing the current state of a template."""
        version_obj = TemplateVersion(
            version=template.version,
            template_id=template.template_id,
            steps=template.steps,
            changelog=changelog,
            created_at=datetime.utcnow().isoformat(),
        )
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO template_versions
                (version, template_id, steps, changelog, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    version_obj.version,
                    version_obj.template_id,
                    json.dumps(version_obj.steps),
                    version_obj.changelog,
                    version_obj.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        return version_obj

    def list_versions(self, template_id: str) -> List[TemplateVersion]:
        """Lists all snapshots saved for the specified template."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM template_versions WHERE template_id = ?", (template_id,))
            rows = cursor.fetchall()
            versions = []
            for r in rows:
                versions.append(
                    TemplateVersion(
                        version=r["version"],
                        template_id=r["template_id"],
                        steps=json.loads(r["steps"]),
                        changelog=r["changelog"],
                        created_at=r["created_at"],
                    )
                )
            return versions
        except Exception:
            return []
        finally:
            conn.close()
