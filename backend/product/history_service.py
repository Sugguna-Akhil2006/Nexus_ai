"""SQLite-backed analysis history service for the Product Experience Layer.

Stores, retrieves, searches, filters, sorts, pins, favorites, and deletes
analysis history records across all intelligence domains (Resume, GitHub,
Document) in a shared SQLite table.

Classes
-------
- HistoryRecord  : Pydantic model representing a single history entry.
- HistoryService : Thread-safe history management with rich query support.

Example usage::

    svc = HistoryService()
    record_id = svc.save_report(report, report_type="resume", workspace_id="ws-1")
    records = svc.search(workspace_id="ws-1", query="engineer")
    svc.pin(record_id)
    svc.favorite(record_id)
    svc.delete(record_id)
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.api.sqlite_mock import DBStorage


# ------------------------------------------------------------------
# HistoryRecord Model
# ------------------------------------------------------------------


class HistoryRecord(BaseModel):
    """Represents a single entry in the cross-domain analysis history store.

    Attributes:
        record_id: Unique history entry identifier.
        report_id: Original report identifier from the intelligence domain.
        report_type: Domain label ('resume', 'github', 'document', etc.).
        title: Human-readable display title.
        workspace_id: Owning workspace identifier.
        user_id: Authoring user identifier.
        created_at: UTC timestamp of report creation.
        is_pinned: Whether the entry is pinned at the top of history lists.
        is_favorite: Whether the entry is marked as a favorite.
        summary: Short excerpt or executive summary text.
        score: Optional primary numeric score (ATS score, quality score).
        metadata: Arbitrary domain-specific metadata.
        tags: Optional searchable tags.
    """

    record_id: str
    report_id: str
    report_type: str
    title: str
    workspace_id: str
    user_id: str = "admin"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_pinned: bool = False
    is_favorite: bool = False
    summary: str = ""
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


# ------------------------------------------------------------------
# HistoryService
# ------------------------------------------------------------------


class HistoryService:
    """Thread-safe SQLite-backed analysis history manager.

    Provides the full CRUD, search, filter, sort, pin, and favorite
    operations needed by the product history UI.

    The singleton pattern ensures the same DB connection pool and
    schema initialization happens only once per process.
    """

    _instance: Optional["HistoryService"] = None
    _class_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "HistoryService":
        with cls._class_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                instance._lock = threading.RLock()
                instance._db = DBStorage()
                instance._init_schema()
                cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_schema(self) -> None:
        """Ensures the product_history table exists."""
        conn = self._db._get_connection()
        try:
            with self._lock:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS product_history (
                        record_id   TEXT PRIMARY KEY,
                        report_id   TEXT NOT NULL,
                        report_type TEXT NOT NULL,
                        title       TEXT NOT NULL,
                        workspace_id TEXT NOT NULL,
                        user_id     TEXT NOT NULL DEFAULT 'admin',
                        created_at  TEXT NOT NULL,
                        is_pinned   INTEGER NOT NULL DEFAULT 0,
                        is_favorite INTEGER NOT NULL DEFAULT 0,
                        summary     TEXT NOT NULL DEFAULT '',
                        score       REAL,
                        metadata    TEXT NOT NULL DEFAULT '{}',
                        tags        TEXT NOT NULL DEFAULT '[]'
                    )
                """)
                conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Write Operations
    # ------------------------------------------------------------------

    def save_report(
        self,
        report: Any,
        report_type: str,
        workspace_id: str,
        user_id: str = "admin",
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Persists an intelligence report as a history record.

        Extracts summary and score from well-known report attributes when
        available, falling back to empty defaults gracefully.

        Args:
            report: Any intelligence report object (Pydantic model).
            report_type: Domain label ('resume', 'github', 'document').
            workspace_id: Owning workspace ID.
            user_id: Authoring user ID.
            title: Optional display title override.
            tags: Optional list of searchable tags.

        Returns:
            The new record_id string.
        """
        record_id = f"hist-{str(uuid.uuid4())[:12]}"
        report_id = getattr(report, "report_id", record_id)

        # Extract summary
        summary = (
            getattr(report, "executive_summary", None)
            or getattr(report, "summary", None)
            or ""
        )
        if hasattr(summary, "executive"):
            summary = summary.executive
        summary = str(summary)[:500]

        # Extract score
        score: Optional[float] = (
            getattr(report, "ats_score", None)
            or getattr(report, "overall_score", None)
        )

        # Build title
        if title is None:
            repo = getattr(report, "repository", None)
            doc_ids = getattr(report, "document_ids", None)
            if repo:
                title = f"GitHub: {repo}"
            elif doc_ids:
                title = f"Document Analysis ({len(doc_ids)} docs)"
            else:
                title = f"{report_type.title()} Report — {report_id[:8]}"

        # Serialize lightweight metadata
        meta: Dict[str, Any] = {"report_type": report_type}
        if score is not None:
            meta["score"] = score

        record = HistoryRecord(
            record_id=record_id,
            report_id=report_id,
            report_type=report_type,
            title=title,
            workspace_id=workspace_id,
            user_id=user_id,
            summary=summary,
            score=score,
            metadata=meta,
            tags=tags or [],
        )

        conn = self._db._get_connection()
        try:
            with self._lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO product_history
                    (record_id, report_id, report_type, title, workspace_id, user_id,
                     created_at, is_pinned, is_favorite, summary, score, metadata, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        record.record_id,
                        record.report_id,
                        record.report_type,
                        record.title,
                        record.workspace_id,
                        record.user_id,
                        record.created_at.isoformat(),
                        int(record.is_pinned),
                        int(record.is_favorite),
                        record.summary,
                        record.score,
                        json.dumps(record.metadata),
                        json.dumps(record.tags),
                    ),
                )
                conn.commit()
        finally:
            conn.close()

        return record_id

    def update_record(self, record: HistoryRecord) -> bool:
        """Updates a full history record in the database.

        Args:
            record: Updated HistoryRecord to persist.

        Returns:
            True if the record existed and was updated.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                cur = conn.execute(
                    """
                    UPDATE product_history
                    SET title=?, is_pinned=?, is_favorite=?, summary=?, tags=?
                    WHERE record_id=?
                    """,
                    (
                        record.title,
                        int(record.is_pinned),
                        int(record.is_favorite),
                        record.summary,
                        json.dumps(record.tags),
                        record.record_id,
                    ),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def delete(self, record_id: str) -> bool:
        """Deletes a single history record by ID.

        Args:
            record_id: Target record identifier.

        Returns:
            True if deleted, False if not found.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                cur = conn.execute(
                    "DELETE FROM product_history WHERE record_id = ?",
                    (record_id,),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def bulk_delete(self, record_ids: List[str]) -> int:
        """Deletes multiple history records by ID.

        Args:
            record_ids: List of record IDs to delete.

        Returns:
            Number of records successfully deleted.
        """
        if not record_ids:
            return 0
        placeholders = ",".join("?" * len(record_ids))
        conn = self._db._get_connection()
        try:
            with self._lock:
                cur = conn.execute(
                    f"DELETE FROM product_history WHERE record_id IN ({placeholders})",
                    record_ids,
                )
                conn.commit()
                return cur.rowcount
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Pin / Favorite
    # ------------------------------------------------------------------

    def pin(self, record_id: str, pinned: bool = True) -> bool:
        """Toggles the pinned state of a history record.

        Args:
            record_id: Target record identifier.
            pinned: True to pin, False to unpin.

        Returns:
            True on success, False if not found.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                cur = conn.execute(
                    "UPDATE product_history SET is_pinned = ? WHERE record_id = ?",
                    (int(pinned), record_id),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    def favorite(self, record_id: str, favorited: bool = True) -> bool:
        """Toggles the favorite state of a history record.

        Args:
            record_id: Target record identifier.
            favorited: True to mark as favorite, False to unmark.

        Returns:
            True on success, False if not found.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                cur = conn.execute(
                    "UPDATE product_history SET is_favorite = ? WHERE record_id = ?",
                    (int(favorited), record_id),
                )
                conn.commit()
                return cur.rowcount > 0
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Read Operations
    # ------------------------------------------------------------------

    def get(self, record_id: str) -> Optional[HistoryRecord]:
        """Retrieves a single history record by ID.

        Args:
            record_id: Target record identifier.

        Returns:
            HistoryRecord if found, else None.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                row = conn.execute(
                    "SELECT * FROM product_history WHERE record_id = ?",
                    (record_id,),
                ).fetchone()
        finally:
            conn.close()
        return self._row_to_record(row) if row else None

    def list(
        self,
        workspace_id: str,
        report_type: Optional[str] = None,
        pinned_only: bool = False,
        favorites_only: bool = False,
        sort_by: str = "created_at",
        sort_desc: bool = True,
        limit: int = 50,
        offset: int = 0,
    ) -> List[HistoryRecord]:
        """Lists history records with optional filtering and sorting.

        Args:
            workspace_id: Filter by workspace.
            report_type: Optional domain type filter.
            pinned_only: When True, only return pinned records.
            favorites_only: When True, only return favorite records.
            sort_by: Column to sort by ('created_at', 'score', 'title').
            sort_desc: True for descending, False for ascending.
            limit: Maximum number of records to return.
            offset: Pagination offset.

        Returns:
            List of matching HistoryRecord instances.
        """
        allowed_sort = {"created_at", "score", "title", "report_type"}
        if sort_by not in allowed_sort:
            sort_by = "created_at"
        direction = "DESC" if sort_desc else "ASC"

        conditions = ["workspace_id = ?"]
        params: List[Any] = [workspace_id]

        if report_type:
            conditions.append("report_type = ?")
            params.append(report_type)
        if pinned_only:
            conditions.append("is_pinned = 1")
        if favorites_only:
            conditions.append("is_favorite = 1")

        # Pinned records always appear first
        order_clause = f"is_pinned DESC, {sort_by} {direction}"
        where_clause = " AND ".join(conditions)

        sql = (
            f"SELECT * FROM product_history WHERE {where_clause} "
            f"ORDER BY {order_clause} LIMIT ? OFFSET ?"
        )
        params += [limit, offset]

        conn = self._db._get_connection()
        try:
            with self._lock:
                rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [r for r in (self._row_to_record(row) for row in rows) if r]

    def search(
        self,
        workspace_id: str,
        query: str,
        report_type: Optional[str] = None,
        limit: int = 30,
    ) -> List[HistoryRecord]:
        """Full-text search across title, summary, and tags columns.

        Args:
            workspace_id: Filter by workspace.
            query: Search query string.
            report_type: Optional domain type filter.
            limit: Maximum number of results.

        Returns:
            List of matching HistoryRecord instances.
        """
        like_query = f"%{query}%"
        conditions = [
            "workspace_id = ?",
            "(title LIKE ? OR summary LIKE ? OR tags LIKE ?)",
        ]
        params: List[Any] = [workspace_id, like_query, like_query, like_query]

        if report_type:
            conditions.append("report_type = ?")
            params.append(report_type)

        where_clause = " AND ".join(conditions)
        sql = (
            f"SELECT * FROM product_history WHERE {where_clause} "
            f"ORDER BY is_pinned DESC, created_at DESC LIMIT ?"
        )
        params.append(limit)

        conn = self._db._get_connection()
        try:
            with self._lock:
                rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [r for r in (self._row_to_record(row) for row in rows) if r]

    def count(self, workspace_id: str) -> Dict[str, int]:
        """Returns per-type counts of history records for a workspace.

        Args:
            workspace_id: Target workspace identifier.

        Returns:
            Dict mapping report_type to record count.
        """
        conn = self._db._get_connection()
        try:
            with self._lock:
                rows = conn.execute(
                    """
                    SELECT report_type, COUNT(*) as cnt
                    FROM product_history
                    WHERE workspace_id = ?
                    GROUP BY report_type
                    """,
                    (workspace_id,),
                ).fetchall()
        finally:
            conn.close()
        return {row["report_type"]: row["cnt"] for row in rows}

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_record(row: Any) -> Optional[HistoryRecord]:
        """Converts a SQLite row dict to a HistoryRecord.

        Args:
            row: sqlite3.Row object.

        Returns:
            HistoryRecord, or None on parse failure.
        """
        try:
            return HistoryRecord(
                record_id=row["record_id"],
                report_id=row["report_id"],
                report_type=row["report_type"],
                title=row["title"],
                workspace_id=row["workspace_id"],
                user_id=row["user_id"],
                created_at=datetime.fromisoformat(row["created_at"]),
                is_pinned=bool(row["is_pinned"]),
                is_favorite=bool(row["is_favorite"]),
                summary=row["summary"] or "",
                score=row["score"],
                metadata=json.loads(row["metadata"] or "{}"),
                tags=json.loads(row["tags"] or "[]"),
            )
        except Exception:
            return None
