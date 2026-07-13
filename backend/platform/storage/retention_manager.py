"""Retention manager cleaning up old files exceeding storage lifecycles."""

import os
import time
from typing import List, Dict, Any
from backend.platform.storage.file_storage import FileStorage


class RetentionManager:
    """Monitors local storage dirs, purging files that exceed threshold ages."""

    def __init__(self, storage: FileStorage, retention_days: int = 30) -> None:
        """Initializes settings.

        Args:
            storage: Local storage manager.
            retention_days: Number of days before a file is considered stale.
        """
        self.storage = storage
        self.retention_seconds = retention_days * 86400

    def purge_expired_files(self) -> List[str]:
        """Scans the storage directory and deletes files older than retention policy.

        Returns:
            A list of deleted file identifiers.
        """
        deleted = []
        now = time.time()
        root = self.storage.root_dir

        if not os.path.exists(root):
            return deleted

        for filename in os.listdir(root):
            path = os.path.join(root, filename)
            if os.path.isfile(path):
                stat = os.stat(path)
                # Check modification time
                mtime = stat.st_mtime
                if (now - mtime) > self.retention_seconds:
                    try:
                        os.remove(path)
                        deleted.append(filename)
                    except Exception:
                        pass
        return deleted
