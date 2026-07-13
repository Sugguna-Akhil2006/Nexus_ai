"""Checks database and cache connection status for health monitoring."""

import sqlite3
from typing import Dict, Any


class HealthMonitor:
    """Probes databases and cache backends to check operational status."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        """Initializes settings.

        Args:
            db_path: Path to database.
        """
        self.db_path = db_path

    def check_database(self) -> Dict[str, Any]:
        """Probes the SQL database.

        Returns:
            Status dictionary.
        """
        try:
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_redis(self, host: str = "localhost", port: int = 6379) -> Dict[str, Any]:
        """Probes the Redis cache.

        Returns:
            Status dictionary.
        """
        try:
            import redis
            r = redis.Redis(host=host, port=port, socket_timeout=2.0)
            r.ping()
            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
