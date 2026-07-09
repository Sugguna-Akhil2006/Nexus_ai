"""Snapshot manager creating full, incremental, and metadata backup archives."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.recovery.checkpoint_store import CheckpointStore
from backend.recovery.models import BackupRecord, BackupType, CheckpointType


class SnapshotManager:
    """Creates and catalogues backup snapshots from checkpoint data.

    Backups are written as JSON files in the designated snapshot directory.
    Metadata, incremental, and full backup strategies are all supported.
    Thread safety is guaranteed via a reentrant lock.
    """

    def __init__(
        self,
        store: CheckpointStore,
        snapshot_dir: str = "recovery_snapshots",
    ) -> None:
        self._lock = threading.RLock()
        self._store = store
        self._snapshot_dir = snapshot_dir
        self._history: List[BackupRecord] = []
        os.makedirs(self._snapshot_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def take_full_backup(self, label: str = "") -> BackupRecord:
        """Creates a full backup of all current checkpoints.

        Args:
            label: Optional human-readable tag stored in metadata.

        Returns:
            :class:`BackupRecord` describing the archive.
        """
        with self._lock:
            checkpoints = self._store.list_all()
            return self._write_backup(
                backup_type=BackupType.FULL,
                checkpoints_data=[c.model_dump() for c in checkpoints],
                checkpoint_ids=[c.checkpoint_id for c in checkpoints],
                label=label or "full_backup",
            )

    def take_incremental_backup(
        self, since_backup_id: Optional[str] = None
    ) -> BackupRecord:
        """Creates an incremental backup of checkpoints not in a previous backup.

        For simplicity this implementation backs up all checkpoints of
        KNOWLEDGE and EXECUTION_CONTEXT types (most volatile).

        Args:
            since_backup_id: Previous backup ID (informational).

        Returns:
            :class:`BackupRecord`.
        """
        with self._lock:
            volatile_types = [CheckpointType.KNOWLEDGE, CheckpointType.EXECUTION_CONTEXT]
            checkpoints = []
            for ctype in volatile_types:
                checkpoints.extend(self._store.list_by_type(ctype))
            return self._write_backup(
                backup_type=BackupType.INCREMENTAL,
                checkpoints_data=[c.model_dump() for c in checkpoints],
                checkpoint_ids=[c.checkpoint_id for c in checkpoints],
                label="incremental",
                extra_meta={"since_backup_id": since_backup_id or ""},
            )

    def take_metadata_backup(self) -> BackupRecord:
        """Creates a metadata-only backup (configuration and session checkpoints).

        Returns:
            :class:`BackupRecord`.
        """
        with self._lock:
            meta_types = [CheckpointType.CONFIGURATION, CheckpointType.SESSION]
            checkpoints = []
            for ctype in meta_types:
                checkpoints.extend(self._store.list_by_type(ctype))
            return self._write_backup(
                backup_type=BackupType.METADATA,
                checkpoints_data=[c.model_dump() for c in checkpoints],
                checkpoint_ids=[c.checkpoint_id for c in checkpoints],
                label="metadata",
            )

    def list_backups(self) -> List[BackupRecord]:
        """Returns all backup records, newest first."""
        with self._lock:
            return list(reversed(self._history))

    def get_backup(self, backup_id: str) -> Optional[BackupRecord]:
        """Retrieves a backup record by ID."""
        with self._lock:
            for record in self._history:
                if record.backup_id == backup_id:
                    return record
            return None

    def load_backup_data(self, backup_id: str) -> List[Dict]:
        """Loads the raw checkpoint data from a backup archive file.

        Args:
            backup_id: Target backup identifier.

        Returns:
            List of raw checkpoint dictionaries.

        Raises:
            FileNotFoundError: If archive does not exist.
        """
        path = os.path.join(self._snapshot_dir, f"{backup_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Backup archive not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("checkpoints", [])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _write_backup(
        self,
        backup_type: BackupType,
        checkpoints_data: List[Dict],
        checkpoint_ids: List[str],
        label: str = "",
        extra_meta: Optional[Dict] = None,
    ) -> BackupRecord:
        backup_id = str(uuid.uuid4())[:12]
        ts = datetime.now(timezone.utc).isoformat()
        archive = {
            "backup_id": backup_id,
            "backup_type": backup_type.value,
            "created_at": ts,
            "label": label,
            "checkpoints": checkpoints_data,
        }
        path = os.path.join(self._snapshot_dir, f"{backup_id}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(archive, fh, indent=2)

        raw = json.dumps(archive).encode()
        record = BackupRecord(
            backup_id=backup_id,
            backup_type=backup_type,
            components=list({c.get("component_id", "") for c in checkpoints_data}),
            checkpoint_ids=checkpoint_ids,
            size_bytes=len(raw),
            created_at=ts,
            metadata={"label": label, **(extra_meta or {})},
        )
        self._history.append(record)
        return record
