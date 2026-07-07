"""Execution history tracking module managing persistent logs and exports (JSON, CSV, Markdown)."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List

from backend.api.sqlite_mock import DBStorage
from backend.diagnostics.models import RequestTrace


class ExecutionHistory:
    """Manages persistence of request traces and formats exports."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS diagnostic_traces (
                request_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                modules_used TEXT NOT NULL,
                providers_used TEXT NOT NULL,
                retries INTEGER NOT NULL,
                errors TEXT NOT NULL,
                timeline TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def save_trace(self, trace: RequestTrace) -> None:
        """Saves a RequestTrace model instance to SQLite."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO diagnostic_traces 
                (request_id, workspace_id, user_id, status, duration_ms, modules_used, providers_used, retries, errors, timeline, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.request_id,
                    trace.workspace_id,
                    trace.user_id,
                    trace.status,
                    trace.duration_ms,
                    json.dumps(trace.modules_used),
                    json.dumps(trace.providers_used),
                    trace.retries,
                    json.dumps(trace.errors),
                    json.dumps([s.model_dump() for s in trace.timeline]),
                    trace.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def list_traces(self) -> List[Dict[str, Any]]:
        """Retrieves all serialized request traces from database."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM diagnostic_traces ORDER BY created_at DESC")
            rows = cursor.fetchall()
            traces = []
            for r in rows:
                traces.append({
                    "request_id": r["request_id"],
                    "workspace_id": r["workspace_id"],
                    "user_id": r["user_id"],
                    "status": r["status"],
                    "duration_ms": r["duration_ms"],
                    "modules_used": json.loads(r["modules_used"]),
                    "providers_used": json.loads(r["providers_used"]),
                    "retries": r["retries"],
                    "errors": json.loads(r["errors"]),
                    "timeline": json.loads(r["timeline"]),
                    "created_at": r["created_at"],
                })
            return traces
        except Exception:
            return []
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Exports
    # ------------------------------------------------------------------

    def export_json(self, traces: List[Dict[str, Any]]) -> str:
        """Formats traces list into standard JSON export."""
        return json.dumps(traces, indent=2, default=str)

    def export_csv(self, traces: List[Dict[str, Any]]) -> str:
        """Formats traces list into CSV export."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Request ID", "Workspace", "User", "Status", "Duration (ms)",
            "Modules Used", "Providers Used", "Retries", "Created At"
        ])
        for t in traces:
            writer.writerow([
                t["request_id"],
                t["workspace_id"],
                t["user_id"],
                t["status"],
                t["duration_ms"],
                ", ".join(t["modules_used"]),
                ", ".join(t["providers_used"]),
                t["retries"],
                t["created_at"],
            ])
        return output.getvalue()

    def export_markdown(self, traces: List[Dict[str, Any]]) -> str:
        """Formats traces list into Markdown table report."""
        lines = [
            "# Diagnostics Execution History Report\n",
            "| Request ID | Workspace | User | Status | Duration (ms) | Created At |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for t in traces:
            lines.append(
                f"| `{t['request_id']}` | {t['workspace_id']} | {t['user_id']} | "
                f"{t['status']} | {t['duration_ms']:.1f} | {t['created_at']} |"
            )
        return "\n".join(lines)
