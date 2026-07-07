"""Memory Inspector retrieving short-term variables, long-term logs, and profiles."""

from __future__ import annotations

from typing import Optional

from backend.api.sqlite_mock import DBStorage
from backend.studio.models import MemorySnapshot


class MemoryInspector:
    """Inspects workspace memory contexts and knowledge profiles."""

    def __init__(self) -> None:
        self._db = DBStorage()

    def get_memory_snapshot(self, workspace_id: str) -> MemorySnapshot:
        """Compiles memory variables snapshot for the given workspace isolation context."""
        short_term = {}
        long_term = {}
        knowledge_profile = {}

        # 1. Fetch knowledge profile (documents list as proxy info)
        conn = self._db._get_connection()
        try:
            docs = conn.execute(
                "SELECT * FROM documents WHERE workspace_id = ?",
                (workspace_id,)
            ).fetchall()
            for d in docs:
                knowledge_profile[d["document_id"]] = {
                    "name": d["name"],
                    "status": d["status"],
                    "checksum": d["checksum"]
                }

            # 2. Simulate short term state variables
            short_term = {
                "active_session": True,
                "current_cursor_pos": 74,
                "loaded_agent": "ProfessionalAgent"
            }

            # 3. Simulate long term profile attributes
            long_term = {
                "total_documents_ingested": len(docs),
                "workspace_creation_date": "2026-07-07"
            }
        except Exception:
            pass
        finally:
            conn.close()

        return MemorySnapshot(
            workspace_id=workspace_id,
            short_term=short_term,
            long_term=long_term,
            knowledge_profile=knowledge_profile,
            memory_usage_bytes=1024 * (len(knowledge_profile) + 1)
        )
