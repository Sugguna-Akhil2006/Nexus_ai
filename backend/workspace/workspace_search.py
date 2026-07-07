"""Workspace Search service querying documents, reports, repositories, and histories."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import json

from backend.api.sqlite_mock import DBStorage
from backend.workspace.workspace_models import SearchResultItem


class WorkspaceSearchService:
    """Performs unified search across multiple database tables to locate resources."""

    def __init__(self) -> None:
        self._db = DBStorage()

    def search(self, workspace_id: str, query: str, types: Optional[List[str]] = None, limit: int = 20) -> List[SearchResultItem]:
        """Queries multiple resource tables (documents, history, conversations) and compiles results."""
        if not types:
            types = ["document", "report", "repository", "history"]

        results: List[SearchResultItem] = []
        like_query = f"%{query}%"
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()

            # 1. Search Documents table
            if "document" in types:
                cursor.execute(
                    """
                    SELECT document_id, name, created_at
                    FROM documents
                    WHERE workspace_id = ? AND (name LIKE ? OR checksum LIKE ?)
                    LIMIT ?
                    """,
                    (workspace_id, like_query, like_query, limit)
                )
                for r in cursor.fetchall():
                    dt = datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc)
                    results.append(SearchResultItem(
                        id=r["document_id"],
                        name=r["name"],
                        type="document",
                        snippet=f"Uploaded document: {r['name']}",
                        workspace_id=workspace_id,
                        created_at=dt,
                        metadata={}
                    ))

            # 2. Search product_history table (Resume, GitHub, Document reports)
            if "report" in types or "history" in types:
                # Check if product_history table exists first
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_history'")
                if cursor.fetchone():
                    cursor.execute(
                        """
                        SELECT record_id, report_id, report_type, title, summary, created_at
                        FROM product_history
                        WHERE workspace_id = ? AND (title LIKE ? OR summary LIKE ? OR tags LIKE ?)
                        LIMIT ?
                        """,
                        (workspace_id, like_query, like_query, like_query, limit)
                    )
                    for r in cursor.fetchall():
                        dt = datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc)
                        results.append(SearchResultItem(
                            id=r["record_id"],
                            name=r["title"],
                            type="report" if r["report_type"] != "document" else "document_report",
                            snippet=r["summary"] or f"Analysis result for {r['title']}",
                            workspace_id=workspace_id,
                            created_at=dt,
                            metadata={"report_id": r["report_id"], "report_type": r["report_type"]}
                        ))

            # 3. Search GitHub product history for repositories matching query
            if "repository" in types:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_product_history'")
                if cursor.fetchone():
                    cursor.execute(
                        """
                        SELECT report_id, repository, created_at
                        FROM github_product_history
                        WHERE workspace_id = ? AND repository LIKE ?
                        LIMIT ?
                        """,
                        (workspace_id, like_query, limit)
                    )
                    for r in cursor.fetchall():
                        dt = datetime.fromisoformat(r["created_at"]) if r["created_at"] else datetime.now(timezone.utc)
                        results.append(SearchResultItem(
                            id=r["report_id"],
                            name=f"Repo: {r['repository']}",
                            type="repository",
                            snippet=f"GitHub Repository Analysis for {r['repository']}",
                            workspace_id=workspace_id,
                            created_at=dt,
                            metadata={"repository": r["repository"]}
                        ))

        finally:
            conn.close()

        # Sort by relevance simulated score (defaults to 1.0) and date descending
        results.sort(key=lambda item: item.created_at, reverse=True)
        return results[:limit]
