"""Workspace Dashboard service aggregating stats, recent analyses, activity timelines, and statistics."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, List

from backend.api.sqlite_mock import DBStorage
from backend.workspace.workspace_models import WorkspaceDashboardData, WorkspaceStats, WorkspaceDetail
from backend.workspace.workspace_service import WorkspaceService


class WorkspaceDashboardService:
    """Consolidates dashboard telemetry (stats, documents, repository activity, and timeline)."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._ws_svc = WorkspaceService()

    def get_dashboard(self, workspace_id: str) -> WorkspaceDashboardData:
        """Retrieves and populates full WorkspaceDashboardData payload."""
        ws_detail = self._ws_svc.get_workspace(workspace_id)
        if not ws_detail:
            raise Exception(f"Workspace '{workspace_id}' not found.")

        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()

            # 1. Document count
            cursor.execute("SELECT COUNT(*) FROM documents WHERE workspace_id = ?", (workspace_id,))
            total_docs = cursor.fetchone()[0]

            # 2. Document types distribution (Mock based on name suffix)
            cursor.execute("SELECT name FROM documents WHERE workspace_id = ?", (workspace_id,))
            doc_types = {"pdf": 0, "docx": 0, "txt": 0, "other": 0}
            for row in cursor.fetchall():
                ext = row["name"].split(".")[-1].lower() if "." in row["name"] else "other"
                if ext in doc_types:
                    doc_types[ext] += 1
                else:
                    doc_types["other"] += 1

            # 3. Repository counts
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_product_history'")
            total_repos = 0
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(DISTINCT repository) FROM github_product_history WHERE workspace_id = ?", (workspace_id,))
                total_repos = cursor.fetchone()[0]

            # 4. Total analyses count
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_history'")
            total_analyses = 0
            pinned_reports = []
            recent_analyses = []
            if cursor.fetchone():
                cursor.execute("SELECT COUNT(*) FROM product_history WHERE workspace_id = ?", (workspace_id,))
                total_analyses = cursor.fetchone()[0]

                # Get pinned reports
                cursor.execute(
                    "SELECT record_id, report_id, report_type, title, summary, created_at FROM product_history WHERE workspace_id = ? AND is_pinned = 1 LIMIT 5",
                    (workspace_id,)
                )
                pinned_reports = [dict(r) for r in cursor.fetchall()]

                # Get recent analyses
                cursor.execute(
                    "SELECT record_id, report_id, report_type, title, summary, created_at FROM product_history WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 10",
                    (workspace_id,)
                )
                recent_analyses = [dict(r) for r in cursor.fetchall()]

            # 5. Recent documents
            cursor.execute(
                "SELECT document_id, name, status, created_at FROM documents WHERE workspace_id = ? ORDER BY created_at DESC LIMIT 5",
                (workspace_id,)
            )
            recent_documents = [dict(r) for r in cursor.fetchall()]

            # 6. Timeline activities
            activities = self._ws_svc.get_activities(workspace_id, limit=10)

        finally:
            conn.close()

        # Storage usage mock: estimate 15KB per document
        storage_bytes = total_docs * 15360

        stats = WorkspaceStats(
            total_documents=total_docs,
            total_analyses=total_analyses,
            total_repositories=total_repos,
            ai_usage_count=total_analyses * 3,  # Simulated usage
            storage_used_bytes=storage_bytes,
            document_types=doc_types,
            recent_activity_count=len(activities)
        )

        from backend.workspace.workspace_models import ActivityRecord
        timeline_records = []
        for act in activities:
            dt = datetime.fromisoformat(act["timestamp"]) if act["timestamp"] else datetime.now(timezone.utc)
            timeline_records.append(ActivityRecord(
                activity_id=act["activity_id"],
                workspace_id=act["workspace_id"],
                user_id=act["user_id"],
                activity_type=act["activity_type"],
                description=act["description"],
                timestamp=dt,
                metadata=json.loads(act["metadata"] or "{}")
            ))

        return WorkspaceDashboardData(
            workspace=ws_detail,
            stats=stats,
            recent_analyses=recent_analyses,
            pinned_reports=pinned_reports,
            recent_documents=recent_documents,
            timeline=timeline_records
        )
