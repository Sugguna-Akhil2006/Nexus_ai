"""Latency Predictor calculating expected model response times based on history logs."""

from __future__ import annotations

from typing import Dict

from backend.api.sqlite_mock import DBStorage


class LatencyPredictor:
    """Predicts latencies for models based on SQLite historical records."""

    def __init__(self) -> None:
        self._db = DBStorage()

    def predict_latency_ms(self, model_id: str) -> float:
        """Looks up SQLite logs for historical latency, returning 250ms default if empty."""
        conn = self._db._get_connection()
        try:
            row = conn.execute(
                "SELECT AVG(latency_ms) as avg_latency FROM platform_usage_logs WHERE model_id = ? AND status='success'",
                (model_id,)
            ).fetchone()
            
            if row and row["avg_latency"]:
                return float(row["avg_latency"])
            
            # Seed default fallback estimates
            defaults = {
                "gpt-4": 400.0,
                "claude-3-opus": 300.0,
                "gemini-1.5": 200.0,
                "phi3:mini": 80.0
            }
            return defaults.get(model_id.lower(), 250.0)
        except Exception:
            return 250.0
        finally:
            conn.close()
