"""Usage Analytics module tracking operational query histories and latency charts."""

from __future__ import annotations

import sqlite3
import threading
from typing import Any, Dict, List

from backend.api.sqlite_mock import DBStorage
from backend.platform.models import UsageMetrics


class UsageAnalytics:
    """Tracks queries and model execution frequencies for platform dashboards."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_usage_logs (
                log_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                model_id TEXT NOT NULL,
                provider_id TEXT NOT NULL,
                tokens INTEGER NOT NULL,
                cost REAL NOT NULL,
                latency_ms REAL NOT NULL,
                status TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def log_request(self, model_id: str, provider_id: str, tokens: int, cost: float, latency_ms: float, status: str) -> None:
        """Saves a request metrics record to the analytics DB table."""
        import uuid
        from datetime import datetime
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO platform_usage_logs (log_id, timestamp, model_id, provider_id, tokens, cost, latency_ms, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"log-{uuid.uuid4().hex[:8]}",
                    datetime.utcnow().isoformat(),
                    model_id,
                    provider_id,
                    tokens,
                    cost,
                    latency_ms,
                    status
                ))
                conn.commit()
            finally:
                conn.close()

    def get_metrics_summary(self) -> UsageMetrics:
        """Compiles unified platform usage stats summary."""
        conn = self._db._get_connection()
        try:
            row = conn.execute("""
            SELECT
                COUNT(*) as count,
                SUM(tokens) as total_tokens,
                SUM(cost) as total_cost,
                AVG(latency_ms) as avg_latency,
                SUM(case when status='failed' then 1 else 0 end) as total_errors
            FROM platform_usage_logs
            """).fetchone()

            if not row or row["count"] == 0:
                return UsageMetrics()

            return UsageMetrics(
                total_requests=row["count"] or 0,
                total_tokens=row["total_tokens"] or 0,
                total_cost=row["total_cost"] or 0.0,
                average_latency_ms=row["avg_latency"] or 0.0,
                error_count=row["total_errors"] or 0
            )
        finally:
            conn.close()

    def get_distributions(self) -> Dict[str, Any]:
        """Calculates model and provider query distribution splits."""
        conn = self._db._get_connection()
        try:
            model_rows = conn.execute("SELECT model_id, COUNT(*) as count FROM platform_usage_logs GROUP BY model_id").fetchall()
            provider_rows = conn.execute("SELECT provider_id, COUNT(*) as count FROM platform_usage_logs GROUP BY provider_id").fetchall()

            models_split = {r["model_id"]: r["count"] for r in model_rows}
            providers_split = {r["provider_id"]: r["count"] for r in provider_rows}

            return {
                "model_distribution": models_split,
                "provider_distribution": providers_split
            }
        finally:
            conn.close()

    def clear(self) -> None:
        """Clears usage logs for testing."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM platform_usage_logs")
                conn.commit()
            finally:
                conn.close()
