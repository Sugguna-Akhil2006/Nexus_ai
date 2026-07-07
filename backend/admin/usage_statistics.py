"""Aggregates user, storage, workspace, and reports usage telemetry."""

from typing import Any, Dict, List
from backend.api.sqlite_mock import DBStorage


class UsageStatisticsService:
    """Summarizes storage metrics, workspace allocations per user, and report types totals."""

    def __init__(self) -> None:
        self._db = DBStorage()

    def get_usage_statistics(self) -> Dict[str, Any]:
        """Runs aggregation SQL commands listing total workspaces, users, and storage mappings."""
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()

            # 1. User details list with workspace and reports counts
            cursor.execute("SELECT username, email, role, created_at FROM users")
            users_list = []
            for r in cursor.fetchall():
                username = r["username"]
                
                # Count user workspaces
                cursor.execute("SELECT COUNT(*) FROM members WHERE user_id = ?", (username,))
                ws_count = cursor.fetchone()[0]

                # Count reports from product history
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_history'")
                rep_count = 0
                if cursor.fetchone():
                    cursor.execute("SELECT COUNT(*) FROM product_history WHERE user_id = ?", (username,))
                    rep_count = cursor.fetchone()[0]

                users_list.append({
                    "username": username,
                    "email": r["email"],
                    "role": r["role"],
                    "created_at": r["created_at"],
                    "workspaces_count": ws_count,
                    "reports_count": rep_count,
                    "storage_bytes": ws_count * 15360  # Estimate
                })

            # 2. Total summaries
            cursor.execute("SELECT COUNT(*) FROM workspaces")
            total_workspaces = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM documents")
            total_docs = cursor.fetchone()[0]

            return {
                "total_users": len(users_list),
                "total_workspaces": total_workspaces,
                "total_documents": total_docs,
                "users": users_list,
                "total_storage_bytes": total_docs * 15360
            }
        finally:
            conn.close()
