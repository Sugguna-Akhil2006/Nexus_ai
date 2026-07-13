"""Creates zip/tar snapshots and calculates sha256 checksums."""

import hashlib
import os
import shutil
import tarfile
from typing import Optional


class SnapshotManager:
    """Manages archiving directories and verifying checksum integrity."""

    def create_snapshot(self, src_dir: str, dest_archive: str) -> str:
        """Compresses directory into a tar.gz snapshot.

        Args:
            src_dir: Source directory to archive.
            dest_archive: Target archive path.
        """
        # Ensure parent exists
        os.makedirs(os.path.dirname(dest_archive), exist_ok=True)
        
        with tarfile.open(dest_archive, "w:gz") as tar:
            tar.add(src_dir, arcname=os.path.basename(src_dir))
        return dest_archive

    def verify_checksum(self, file_path: str, expected_hash: str) -> bool:
        """Verifies SHA256 checksum of a snapshot archive.

        Args:
            file_path: Archive file path.
            expected_hash: Expected SHA256 string.
        """
        if not os.path.exists(file_path):
            return False

        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        
        return h.hexdigest() == expected_hash

    def calculate_checksum(self, file_path: str) -> str:
        """Calculates SHA256 checksum.

        Args:
            file_path: Archive path.
        """
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
