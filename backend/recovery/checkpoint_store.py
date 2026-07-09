"""Thread-safe SQLite-backed checkpoint store for persisting component state."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from typing import List, Optional

from backend.recovery.models import Checkpoint, CheckpointType


class CheckpointStore:
    """Persists and retrieves component state checkpoints in SQLite.

    A separate database path is used (default ``recovery.db``) so the
    checkpoint store does not contend with the main application DB.
    The store is thread-safe via a reentrant lock.
    """

    def __init__(self, db_path: str = "recovery.db") -> None:
        self._lock = threading.RLock()
        # Support shared in-memory DB for tests
        if db_path == ":memory:":
            self._db_path = "file::memory:?cache=shared&mode=memory"
            self._is_uri = True
            self._keep_alive = sqlite3.connect(self._db_path, uri=True, check_same_thread=False)
        else:
            self._db_path = db_path
            self._is_uri = False
        self._init_schema()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._is_uri:
            return sqlite3.connect(self._db_path, uri=True, check_same_thread=False)
        return sqlite3.connect(self._db_path, check_same_thread=False)

    def _init_schema(self) -> None:
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    checkpoint_type TEXT NOT NULL,
                    component_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
            """)
            conn.commit()
            conn.close()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def save(self, checkpoint: Checkpoint) -> None:
        """Persists a checkpoint to the store.

        Args:
            checkpoint: The state snapshot to save.
        """
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """
                INSERT OR REPLACE INTO checkpoints
                    (checkpoint_id, checkpoint_type, component_id, state, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    checkpoint.checkpoint_id,
                    checkpoint.checkpoint_type.value,
                    checkpoint.component_id,
                    json.dumps(checkpoint.state),
                    checkpoint.created_at,
                    json.dumps(checkpoint.metadata),
                ),
            )
            conn.commit()
            conn.close()

    def get(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Retrieves a checkpoint by ID.

        Args:
            checkpoint_id: Unique checkpoint identifier.

        Returns:
            :class:`Checkpoint` or None if not found.
        """
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,)
            ).fetchone()
            conn.close()
            if not row:
                return None
            return self._row_to_checkpoint(row)

    def list_by_component(self, component_id: str) -> List[Checkpoint]:
        """Lists all checkpoints for a given component, newest first.

        Args:
            component_id: Component identifier.

        Returns:
            List of :class:`Checkpoint` objects.
        """
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE component_id = ? ORDER BY created_at DESC",
                (component_id,),
            ).fetchall()
            conn.close()
            return [self._row_to_checkpoint(r) for r in rows]

    def list_by_type(self, checkpoint_type: CheckpointType) -> List[Checkpoint]:
        """Lists all checkpoints of a given type, newest first."""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM checkpoints WHERE checkpoint_type = ? ORDER BY created_at DESC",
                (checkpoint_type.value,),
            ).fetchall()
            conn.close()
            return [self._row_to_checkpoint(r) for r in rows]

    def list_all(self) -> List[Checkpoint]:
        """Returns all stored checkpoints, newest first."""
        with self._lock:
            conn = self._get_conn()
            rows = conn.execute(
                "SELECT * FROM checkpoints ORDER BY created_at DESC"
            ).fetchall()
            conn.close()
            return [self._row_to_checkpoint(r) for r in rows]

    def delete(self, checkpoint_id: str) -> None:
        """Removes a checkpoint by ID."""
        with self._lock:
            conn = self._get_conn()
            conn.execute("DELETE FROM checkpoints WHERE checkpoint_id = ?", (checkpoint_id,))
            conn.commit()
            conn.close()

    @staticmethod
    def _row_to_checkpoint(row: tuple) -> Checkpoint:
        return Checkpoint(
            checkpoint_id=row[0],
            checkpoint_type=CheckpointType(row[1]),
            component_id=row[2],
            state=json.loads(row[3]),
            created_at=row[4],
            metadata=json.loads(row[5]),
        )

    @staticmethod
    def generate_id() -> str:
        """Generates a unique checkpoint identifier."""
        return str(uuid.uuid4())[:12]
