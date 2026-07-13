"""Safely restores relational database and workspace directories from compressed snapshots."""

import os
import tarfile
from typing import Tuple


class RestoreManager:
    """Handles restoring database and storage directories from snapshots."""

    def restore_database(self, archive_path: str, dest_db_path: str) -> Tuple[bool, str]:
        """Restores database file.

        Args:
            archive_path: Compressed snapshot archive path.
            dest_db_path: Target database destination.
        """
        if not os.path.exists(archive_path):
            return False, "Backup archive not found"

        try:
            # Clear destination
            if os.path.exists(dest_db_path):
                os.remove(dest_db_path)

            with tarfile.open(archive_path, "r:gz") as tar:
                # Extract members
                tar.extractall(path=os.path.dirname(dest_db_path))
            return True, "Database restored successfully"
        except Exception as e:
            return False, f"Restore failed: {str(e)}"

    def restore_storage(self, archive_path: str, dest_storage_dir: str) -> Tuple[bool, str]:
        """Restores storage files directory.

        Args:
            archive_path: Archive snapshot path.
            dest_storage_dir: Destination directory.
        """
        if not os.path.exists(archive_path):
            return False, "Backup archive not found"

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(path=dest_storage_dir)
            return True, "Storage restored successfully"
        except Exception as e:
            return False, f"Restore failed: {str(e)}"
