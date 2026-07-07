"""Template registry managing database templates storage."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workflow_library.models import TemplateScope, WorkflowTemplate
from backend.workflow_library.workflow_catalog import WorkflowCatalog


class TemplateRegistry:
    """Manages SQLite database storage for reusable workflow templates."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()
        self._seed_builtin_templates()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_templates (
                template_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                steps TEXT NOT NULL,
                variables TEXT NOT NULL,
                scope TEXT NOT NULL,
                version TEXT NOT NULL,
                author TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def _seed_builtin_templates(self) -> None:
        builtins = WorkflowCatalog.get_builtin_templates()
        for b in builtins:
            self.save_template(b)

    def save_template(self, template: WorkflowTemplate) -> None:
        """Saves or updates a workflow template record."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_templates
                (template_id, name, description, steps, variables, scope, version, author, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    template.template_id,
                    template.name,
                    template.description,
                    json.dumps(template.steps),
                    json.dumps(template.variables),
                    template.scope.value,
                    template.version,
                    template.author,
                    template.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Retrieves a workflow template by ID."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflow_templates WHERE template_id = ?", (template_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return WorkflowTemplate(
                template_id=r["template_id"],
                name=r["name"],
                description=r["description"],
                steps=json.loads(r["steps"]),
                variables=json.loads(r["variables"]),
                scope=TemplateScope(r["scope"]),
                version=r["version"],
                author=r["author"],
                created_at=r["created_at"],
            )
        except Exception:
            return None
        finally:
            conn.close()

    def list_templates(self) -> List[WorkflowTemplate]:
        """Lists all stored workflow templates."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workflow_templates")
            rows = cursor.fetchall()
            templates = []
            for r in rows:
                templates.append(
                    WorkflowTemplate(
                        template_id=r["template_id"],
                        name=r["name"],
                        description=r["description"],
                        steps=json.loads(r["steps"]),
                        variables=json.loads(r["variables"]),
                        scope=TemplateScope(r["scope"]),
                        version=r["version"],
                        author=r["author"],
                        created_at=r["created_at"],
                    )
                )
            return templates
        except Exception:
            return []
        finally:
            conn.close()

    def delete_template(self, template_id: str) -> None:
        """Deletes a template from SQLite."""
        conn = self.db._get_connection()
        try:
            conn.execute("DELETE FROM workflow_templates WHERE template_id = ?", (template_id,))
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()
