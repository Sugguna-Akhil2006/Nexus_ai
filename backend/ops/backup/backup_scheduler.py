"""Schedules automatic backups of the database and storage directories."""

import os
import time
import threading
from typing import List, Optional

from backend.ops.backup.snapshot_manager import SnapshotManager


class BackupScheduler:
    """Orchestrates periodic backup snapshots."""

    def __init__(self, backup_dir: str = "backups", interval_seconds: float = 86400.0) -> None:
        """Initializes settings.

        Args:
            backup_dir: Directory where backups are written.
            interval_seconds: Backup frequency in seconds.
        """
        self.backup_dir = backup_dir
        self.interval = interval_seconds
        self.snapshot = SnapshotManager()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def trigger_backup(self, db_file: str, storage_dir: str) -> List[str]:
        """Creates backup files for database and storage directories.

        Args:
            db_file: Relational SQLite database path.
            storage_dir: Storage files directory.
        """
        timestamp = int(time.time())
        db_archive = os.path.join(self.backup_dir, f"nexus_db_{timestamp}.tar.gz")
        storage_archive = os.path.join(self.backup_dir, f"nexus_storage_{timestamp}.tar.gz")
        
        created = []
        if os.path.exists(db_file):
            self.snapshot.create_snapshot(db_file, db_archive)
            created.append(db_archive)

        if os.path.exists(storage_dir):
            self.snapshot.create_snapshot(storage_dir, storage_archive)
            created.append(storage_archive)

        return created

    def start(self, db_file: str, storage_dir: str) -> None:
        """Starts background periodic backup checks."""
        with self._lock:
            if self._running:
                return
            self._running = True
        self._thread = threading.Thread(
            target=self._scheduler_loop,
            args=(db_file, storage_dir),
            daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Stops background checks."""
        with self._lock:
            self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def _scheduler_loop(self, db_file: str, storage_dir: str) -> None:
        """Loops checking timestamps."""
        while True:
            with self._lock:
                if not self._running:
                    break
            
            try:
                self.trigger_backup(db_file, storage_dir)
            except Exception:
                pass
            
            # Wait for next interval
            time.sleep(self.interval)
