"""Manages history tables, SQL queries, and diffing algorithms for Document reports."""

import json
from typing import Dict, List, Any, Optional
from backend.api.sqlite_mock import DBStorage
from backend.intelligence.document.document_model import DocumentAnalysisReport
from backend.intelligence.document.models import DocumentKnowledgeReport


class DocumentHistoryManager:
    """Manages history tables, SQL queries, and diffing algorithms for Document reports."""

    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        """Initializes sqlite table for product level report history."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS document_product_history (
                    report_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    document_ids TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def save_report(self, report: Any) -> None:
        """Saves a compiled report to SQLite."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO document_product_history 
                    (report_id, workspace_id, document_ids, report_data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        report.report_id,
                        report.workspace_id,
                        ",".join(report.document_ids),
                        report.model_dump_json(),
                        report.analyzed_at.isoformat()
                    )
                )
                conn.commit()
        finally:
            conn.close()

    def get_report(self, report_id: str) -> Optional[DocumentAnalysisReport]:
        """Retrieves report from DB."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT report_data FROM document_product_history WHERE report_id = ?",
                (report_id,)
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return DocumentAnalysisReport.model_validate(data)
            return None
        finally:
            conn.close()

    def get_knowledge_report(self, report_id: str) -> Optional[DocumentKnowledgeReport]:
        """Retrieves knowledge report from DB."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT report_data FROM document_product_history WHERE report_id = ?",
                (report_id,)
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return DocumentKnowledgeReport.model_validate(data)
            return None
        finally:
            conn.close()

    def list_history(self, workspace_id: str) -> List[DocumentAnalysisReport]:
        """Lists all reports under a workspace."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT report_data FROM document_product_history WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,)
            )
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                data = json.loads(row[0])
                # Check structure type
                if "knowledge_graph" in data:
                    reports.append(DocumentKnowledgeReport.model_validate(data))
                else:
                    reports.append(DocumentAnalysisReport.model_validate(data))
            return reports
        finally:
            conn.close()

    def compare_reports(self, base: Any, target: Any) -> Dict[str, Any]:
        """Computes diff metrics between two Document reports."""
        base_words = sum(meta.word_count for meta in base.metadata.values())
        target_words = sum(meta.word_count for meta in target.metadata.values())
        
        base_lines = sum(meta.line_count for meta in base.metadata.values())
        target_lines = sum(meta.line_count for meta in target.metadata.values())
        
        base_kws = set()
        for meta in base.metadata.values():
            base_kws.update(meta.keywords)
            
        target_kws = set()
        for meta in target.metadata.values():
            target_kws.update(meta.keywords)

        new_kws = list(target_kws - base_kws)
        removed_kws = list(base_kws - target_kws)

        return {
            "base_report_id": base.report_id,
            "target_report_id": target.report_id,
            "comparison": {
                "word_count": {
                    "base": base_words,
                    "target": target_words,
                    "delta": target_words - base_words
                },
                "line_count": {
                    "base": base_lines,
                    "target": target_lines,
                    "delta": target_lines - base_lines
                },
                "keywords": {
                    "added": new_kws,
                    "removed": removed_kws
                }
            }
        }
