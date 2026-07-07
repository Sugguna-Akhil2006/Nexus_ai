"""Audit logger responsible for recording execution metrics, status, and safety violations."""

from __future__ import annotations

from datetime import datetime
import json
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.governance.models import AuditRecord


class AuditLogger:
    """Thread-safe historical audit logger persisting trails to SQLite database."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_audit_logs (
                record_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                module_used TEXT NOT NULL,
                model_used TEXT NOT NULL,
                provider_used TEXT NOT NULL,
                tokens_consumed INTEGER NOT NULL,
                cost_estimated REAL NOT NULL,
                latency_ms REAL NOT NULL,
                status TEXT NOT NULL,
                policy_violations TEXT NOT NULL,
                security_alerts TEXT NOT NULL,
                risk_level TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_execution(self, record: AuditRecord) -> None:
        """Persists an audit record to the sqlite trail."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO governance_audit_logs (
                    record_id, timestamp, user_id, workspace_id, module_used,
                    model_used, provider_used, tokens_consumed, cost_estimated,
                    latency_ms, status, policy_violations, security_alerts, risk_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.record_id,
                    record.timestamp,
                    record.user_id,
                    record.workspace_id,
                    record.module_used,
                    record.model_used,
                    record.provider_used,
                    record.tokens_consumed,
                    record.cost_estimated,
                    record.latency_ms,
                    record.status,
                    json.dumps(record.policy_violations),
                    json.dumps(record.security_alerts),
                    record.risk_level
                ))
                conn.commit()
            finally:
                conn.close()

    def get_history(self, workspace_id: Optional[str] = None) -> List[AuditRecord]:
        """Retrieves history logs of executed workflows."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                if workspace_id:
                    rows = conn.execute(
                        "SELECT * FROM governance_audit_logs WHERE workspace_id = ? ORDER BY timestamp DESC",
                        (workspace_id,)
                    ).fetchall()
                else:
                    rows = conn.execute("SELECT * FROM governance_audit_logs ORDER BY timestamp DESC").fetchall()
                
                records = []
                for r in rows:
                    try:
                        violations = json.loads(r["policy_violations"])
                    except Exception:
                        violations = r["policy_violations"].split(",") if r["policy_violations"] else []

                    try:
                        alerts = json.loads(r["security_alerts"])
                    except Exception:
                        alerts = r["security_alerts"].split(",") if r["security_alerts"] else []

                    records.append(AuditRecord(
                        record_id=r["record_id"],
                        timestamp=r["timestamp"],
                        user_id=r["user_id"],
                        workspace_id=r["workspace_id"],
                        module_used=r["module_used"],
                        model_used=r["model_used"],
                        provider_used=r["provider_used"],
                        tokens_consumed=r["tokens_consumed"],
                        cost_estimated=r["cost_estimated"],
                        latency_ms=r["latency_ms"],
                        status=r["status"],
                        policy_violations=violations,
                        security_alerts=alerts,
                        risk_level=r["risk_level"]
                    ))
                return records
            finally:
                conn.close()

    def clear(self) -> None:
        """Clears all audit logs for testing purposes."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM governance_audit_logs")
                conn.commit()
            finally:
                conn.close()
