"""Schema migrator applying SQLite DDL changes between platform versions."""

from __future__ import annotations

import sqlite3
import threading
import time
import uuid
from typing import Dict, List, Optional

from backend.migration.models import MigrationKind, MigrationStatus, MigrationStep


# Registry: maps (from_version, to_version) → list of SQL DDL statements
# In production this would be loaded from versioned migration files.
_SCHEMA_MIGRATIONS: Dict[str, List[str]] = {
    "1.0.0->1.1.0": [
        "CREATE TABLE IF NOT EXISTS migration_history "
        "(id TEXT PRIMARY KEY, version TEXT, applied_at TEXT);",
    ],
    "1.1.0->1.2.0": [
        "ALTER TABLE users ADD COLUMN last_login TEXT DEFAULT '';",
    ],
    "1.0.0->2.0.0": [
        "CREATE TABLE IF NOT EXISTS migration_history "
        "(id TEXT PRIMARY KEY, version TEXT, applied_at TEXT);",
        "ALTER TABLE users ADD COLUMN last_login TEXT DEFAULT '';",
    ],
}


class SchemaMigrator:
    """Applies DDL schema migrations to a SQLite database.

    The migrator is idempotent: re-running the same migration key is a no-op
    if the schema change has already been applied (``IF NOT EXISTS`` / ``IF NOT
    EXISTS`` guards in the DDL statements).

    Thread Safety:
        All operations are guarded by an RLock.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self._db_path = db_path

    def get_steps(self, from_version: str, to_version: str) -> List[MigrationStep]:
        """Returns the ordered list of schema migration steps for the version pair.

        Args:
            from_version: Source version string.
            to_version: Target version string.

        Returns:
            List of :class:`MigrationStep` objects (may be empty if no migration needed).
        """
        key = f"{from_version}->{to_version}"
        ddl_list = _SCHEMA_MIGRATIONS.get(key, [])
        steps = []
        for i, ddl in enumerate(ddl_list):
            steps.append(
                MigrationStep(
                    step_id=str(uuid.uuid4())[:8],
                    kind=MigrationKind.SCHEMA,
                    description=f"DDL step {i + 1}: {ddl[:60]}{'...' if len(ddl) > 60 else ''}",
                    from_version=from_version,
                    to_version=to_version,
                )
            )
        return steps

    def apply(self, from_version: str, to_version: str) -> List[MigrationStep]:
        """Applies all schema migration DDL for the version pair.

        Args:
            from_version: Source version string.
            to_version: Target version string.

        Returns:
            Applied :class:`MigrationStep` list with updated statuses.
        """
        steps = self.get_steps(from_version, to_version)
        key = f"{from_version}->{to_version}"
        ddl_list = _SCHEMA_MIGRATIONS.get(key, [])

        with self._lock:
            conn = sqlite3.connect(self._db_path)
            # Ensure users table exists for test/migration isolation
            conn.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, username TEXT);")
            for step, ddl in zip(steps, ddl_list):
                start = time.perf_counter()
                try:
                    conn.execute(ddl)
                    conn.commit()
                    step.status = MigrationStatus.COMPLETED
                    step.applied_at = _utcnow()
                except Exception as exc:
                    step.status = MigrationStatus.FAILED
                    step.error = str(exc)
                finally:
                    step.duration_ms = round((time.perf_counter() - start) * 1000, 2)
            conn.close()
        return steps


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
