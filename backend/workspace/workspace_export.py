"""Workspace Export service compiling workspace assets into formatted zip bundles."""

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.product.export_service import ExportService


class WorkspaceExportService:
    """Collects workspace reports, documents metadata, and exports a ZIP bundle."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._export_svc = ExportService()

    def export_workspace(self, workspace_id: str, formats: Optional[List[str]] = None) -> bytes:
        """Constructs a zip file containing workspace metadata, docs lists, and all reports."""
        formats = formats or ["json", "markdown", "html"]
        
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            conn = self._db._get_connection()
            try:
                cursor = conn.cursor()

                # 1. Fetch workspace detail metadata
                cursor.execute("SELECT name, owner_id, status, created_at FROM workspaces WHERE workspace_id = ?", (workspace_id,))
                ws_row = cursor.fetchone()
                if not ws_row:
                    raise Exception(f"Workspace {workspace_id} not found.")

                workspace_meta = {
                    "workspace_id": workspace_id,
                    "name": ws_row["name"],
                    "owner_id": ws_row["owner_id"],
                    "status": ws_row["status"],
                    "created_at": ws_row["created_at"],
                    "exported_at": datetime.now(timezone.utc).isoformat()
                }
                zf.writestr("workspace_metadata.json", json.dumps(workspace_meta, indent=2))

                # 2. Fetch and list all documents
                cursor.execute("SELECT document_id, name, status, checksum, created_at FROM documents WHERE workspace_id = ?", (workspace_id,))
                docs = [dict(r) for r in cursor.fetchall()]
                zf.writestr("documents_list.json", json.dumps(docs, indent=2))

                # 3. Pull unified reports from product_history and bundle them
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_history'")
                if cursor.fetchone():
                    cursor.execute(
                        "SELECT record_id, report_id, report_type, title, summary, created_at FROM product_history WHERE workspace_id = ?",
                        (workspace_id,)
                    )
                    reports = cursor.fetchall()
                    
                    # Since we can't reconstruct the full pydantic objects easily inside this service
                    # (due to various domain configurations), we bundle a list metadata mapping file
                    # and write the raw text summaries/data inside.
                    reports_summary = []
                    for r in reports:
                        reports_summary.append({
                            "record_id": r["record_id"],
                            "report_id": r["report_id"],
                            "report_type": r["report_type"],
                            "title": r["title"],
                            "summary": r["summary"],
                            "created_at": r["created_at"]
                        })
                    zf.writestr("reports_summary.json", json.dumps(reports_summary, indent=2))
            
            finally:
                conn.close()

        return buffer.getvalue()
