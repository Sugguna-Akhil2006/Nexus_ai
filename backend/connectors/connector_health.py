"""Connector Health monitoring online status and connection latencies."""

from __future__ import annotations

from datetime import datetime
import time
from typing import Dict, Optional

from backend.connectors.connection_pool import ConnectionPool
from backend.connectors.models import ConnectionHealth, ConnectorConfig


class ConnectorHealthMonitor:
    """Evaluates availability metrics for registered connectors."""

    def __init__(self, pool: Optional[ConnectionPool] = None) -> None:
        self.pool = pool or ConnectionPool()

    def check_health(self, config: ConnectorConfig) -> ConnectionHealth:
        """Pings connection endpoints and returns ConnectionHealth logs."""
        start = time.perf_counter()
        try:
            conn = self.pool.get_connection(config)
            is_ok = conn.perform_health_check()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            
            return ConnectionHealth(
                connector_id=config.connector_id,
                status="healthy" if is_ok else "degraded",
                latency_ms=round(elapsed_ms, 2),
                last_check_timestamp=datetime.utcnow()
            )
        except Exception as e:
            return ConnectionHealth(
                connector_id=config.connector_id,
                status="disconnected",
                latency_ms=0.0,
                last_check_timestamp=datetime.utcnow(),
                error_details=str(e)
            )
