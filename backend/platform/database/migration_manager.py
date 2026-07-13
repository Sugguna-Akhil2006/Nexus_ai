"""Migration manager tracking applied schema revisions."""

import os
import time
from typing import List, Dict, Any
from backend.platform.database.connection_pool import ConnectionPool


class MigrationManager:
    """Manages schema creation, migrations track logging table, and version upgrades."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Initializes migration history tracking table.

        Args:
            pool: Connection pool.
        """
        self.pool = pool
        self._init_migration_table()

    def _init_migration_table(self) -> None:
        """Ensures the migrations audit table exists."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
            """)
            conn.commit()
        finally:
            self.pool.release_connection(conn)

    def get_applied_versions(self) -> List[int]:
        """Returns the list of migration versions already applied."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            rows = cursor.fetchall()
            return [r[0] for r in rows]
        finally:
            self.pool.release_connection(conn)

    def apply_migration(self, version: int, name: str, sql_commands: List[str]) -> bool:
        """Applies a migration if not already applied.

        Args:
            version: Unique sequential migration ID.
            name: Description name.
            sql_commands: List of query strings to execute in sequence.
        """
        applied = self.get_applied_versions()
        if version in applied:
            return False

        conn = self.pool.get_connection()
        cursor = conn.cursor()
        try:
            for sql in sql_commands:
                if sql.strip():
                    cursor.execute(sql)
            
            # Log migration application
            import datetime
            timestamp = datetime.datetime.utcnow().isoformat()
            cursor.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) VALUES (?, ?, ?)",
                (version, name, timestamp)
            )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.release_connection(conn)
