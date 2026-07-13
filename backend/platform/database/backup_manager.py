"""Backup manager handling SQL database snapshots and restoring operations."""

import os
import shutil
import sqlite3
from typing import Optional
from backend.platform.database.connection_pool import ConnectionPool


class BackupManager:
    """Provides methods to backup and restore SQLite-based database files."""

    def __init__(self, pool: ConnectionPool, default_backup_dir: str = "backups") -> None:
        """Initializes the backup manager.

        Args:
            pool: Relational connection pool.
            default_backup_dir: Directory where backups are written.
        """
        self.pool = pool
        self.backup_dir = default_backup_dir
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def create_backup(self, dest_filename: str) -> str:
        """Creates a snapshot copy of the active sqlite database.

        Args:
            dest_filename: The target backup filename.
        """
        if self.pool.db_type != "sqlite":
            raise NotImplementedError("Backup currently only supported for SQLite databases.")

        dest_path = os.path.join(self.backup_dir, dest_filename)
        # Using SQLite backup API for online hot-backup support
        src_conn = self.pool.get_connection()
        dest_conn = sqlite3.connect(dest_path)
        try:
            with dest_conn:
                src_conn.backup(dest_conn)
            return dest_path
        finally:
            dest_conn.close()
            src_conn.close()
            self.pool.release_connection(src_conn)

    def restore_backup(self, src_filename: str) -> bool:
        """Restores the database from a backup copy.

        Args:
            src_filename: The name of the backup file in backup_dir.
        """
        if self.pool.db_type != "sqlite":
            raise NotImplementedError("Restore currently only supported for SQLite databases.")

        src_path = os.path.join(self.backup_dir, src_filename)
        if not os.path.exists(src_path):
            return False

        # Terminate active connections in pool to prevent locking
        self.pool.close_all()

        # Copy file over existing DSN path
        db_file = self.pool.dsn
        if os.path.exists(db_file):
            os.remove(db_file)
        
        shutil.copy2(src_path, db_file)
        return True
