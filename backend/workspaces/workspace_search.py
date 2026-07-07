"""Workspace search indexing database queries across projects, reports, and artifacts."""

from __future__ import annotations

from typing import Any, Dict, List

from backend.api.sqlite_mock import DBStorage


class WorkspaceSearch:
    """Performs full text database queries across workspace projects and artifacts."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)

    def search(self, workspace_id: str, query: str) -> List[Dict[str, Any]]:
        """Queries project names, descriptions, and artifact contents matching query terms.

        Args:
            workspace_id: Tenant workspace target scope.
            query: Search query terms.

        Returns:
            List of matched search hit dictionaries.
        """
        if not query:
            return []

        conn = self.db._get_connection()
        hits: List[Dict[str, Any]] = []
        term = f"%{query.lower()}%"

        try:
            cursor = conn.cursor()

            # 1. Search projects
            cursor.execute(
                """
                SELECT project_id, name, description FROM workspace_projects
                WHERE workspace_id = ? AND (lower(name) LIKE ? OR lower(description) LIKE ?)
                """,
                (workspace_id, term, term),
            )
            for r in cursor.fetchall():
                hits.append({
                    "id": r["project_id"],
                    "type": "project",
                    "title": r["name"],
                    "snippet": r["description"] or "",
                })

            # 2. Search artifacts
            cursor.execute(
                """
                SELECT a.artifact_id, a.name, a.artifact_type, a.content, p.name as proj_name 
                FROM project_artifacts a
                JOIN workspace_projects p ON a.project_id = p.project_id
                WHERE p.workspace_id = ? AND (lower(a.name) LIKE ? OR lower(a.content) LIKE ?)
                """,
                (workspace_id, term, term),
            )
            for r in cursor.fetchall():
                hits.append({
                    "id": r["artifact_id"],
                    "type": "artifact",
                    "title": f"{r['proj_name']} / {r['name']}",
                    "snippet": f"[{r['artifact_type']}] {r['content'][:100]}...",
                })

        except Exception:
            pass
        finally:
            conn.close()

        return hits
DefinitionPath = "workspace_search.py"
