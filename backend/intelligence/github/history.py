"""Handles SQL history persistence and provides report comparison/differential tools."""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.intelligence.github.models import GitHubIntelligenceReport


class GitHubHistoryManager:
    """Manages history tables, SQL queries, and diffing algorithms for GitHub reports."""

    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        """Initializes sqlite table for product level report history."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS github_product_history (
                    report_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    repository TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def save_report(self, report: GitHubIntelligenceReport, workspace_id: str) -> None:
        """Saves a compiled report to SQLite."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO github_product_history 
                    (report_id, workspace_id, repository, report_data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        report.report_id,
                        workspace_id,
                        report.repository,
                        report.model_dump_json(),
                        datetime.utcnow().isoformat()
                    )
                )
                conn.commit()
        finally:
            conn.close()

    def get_report(self, report_id: str) -> Optional[GitHubIntelligenceReport]:
        """Loads and parses a report from SQLite."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                row = conn.execute(
                    "SELECT report_data FROM github_product_history WHERE report_id = ?",
                    (report_id,)
                ).fetchone()
                if row:
                    data = json.loads(row["report_data"])
                    return GitHubIntelligenceReport.model_validate(data)
                return None
        finally:
            conn.close()

    def get_history(self, workspace_id: str) -> List[GitHubIntelligenceReport]:
        """Retrieves list of all previously executed analyses."""
        db = DBStorage()
        conn = db._get_connection()
        reports = []
        try:
            with db._lock:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT report_data FROM github_product_history WHERE workspace_id = ? ORDER BY created_at DESC",
                    (workspace_id,)
                )
                rows = cursor.fetchall()
                for r in rows:
                    try:
                        data = json.loads(r["report_data"])
                        reports.append(GitHubIntelligenceReport.model_validate(data))
                    except Exception:
                        pass
        finally:
            conn.close()
        return reports

    def compare_reports(self, report_a: GitHubIntelligenceReport, report_b: GitHubIntelligenceReport) -> Dict[str, Any]:
        """Compares two report metrics and returns delta indicators.

        Calculates LOC diff, maintainability progress, health score growth, and new tech dependencies.
        """
        loc_a = report_a.repository_overview.get("total_lines") or 0
        loc_b = report_b.repository_overview.get("total_lines") or 0
        loc_diff = loc_b - loc_a

        maint_a = report_a.engineering_quality.get("maintainability_score") or 0.0
        maint_b = report_b.engineering_quality.get("maintainability_score") or 0.0
        maint_diff = maint_b - maint_a

        health_a = report_a.repository_health.get("overall_health_score") or 0.0
        health_b = report_b.repository_health.get("overall_health_score") or 0.0
        health_diff = health_b - health_a

        techs_a = set(report_a.technology_stack.get("languages") or []) | set(report_a.technology_stack.get("frameworks") or [])
        techs_b = set(report_b.technology_stack.get("languages") or []) | set(report_b.technology_stack.get("frameworks") or [])
        new_techs = list(techs_b - techs_a)

        return {
            "comparison": {
                "base_report_id": report_a.report_id,
                "target_report_id": report_b.report_id,
                "lines_of_code": {
                    "base": loc_a,
                    "target": loc_b,
                    "delta": loc_diff
                },
                "maintainability_score": {
                    "base": maint_a,
                    "target": maint_b,
                    "delta": round(maint_diff, 1)
                },
                "overall_health_score": {
                    "base": health_a,
                    "target": health_b,
                    "delta": round(health_diff, 1)
                },
                "added_technologies": new_techs
            }
        }
