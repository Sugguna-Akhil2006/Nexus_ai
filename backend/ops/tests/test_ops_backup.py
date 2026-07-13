"""Unit tests for Operations Backups and Restorations package."""

import os
import shutil
import unittest

from backend.ops.backup.snapshot_manager import SnapshotManager
from backend.ops.backup.backup_scheduler import BackupScheduler
from backend.ops.backup.restore_manager import RestoreManager


class TestOpsBackup(unittest.TestCase):
    """Test suite covering backups, restore scripts, and SHA256 validation."""

    def setUp(self) -> None:
        self.test_dir = "test_ops_backup_src"
        os.makedirs(self.test_dir, exist_ok=True)
        with open(os.path.join(self.test_dir, "data.txt"), "w") as f:
            f.write("test data contents")
        self.dest_archive = "test_ops_backups/snapshot.tar.gz"

    def tearDown(self) -> None:
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists("test_ops_backups"):
            shutil.rmtree("test_ops_backups")
        if os.path.exists("test_ops_restored"):
            shutil.rmtree("test_ops_restored")

    def test_snapshot_lifecycle(self) -> None:
        """Verifies directory compression, checksum calculation, and extraction restore checks."""
        sm = SnapshotManager()
        
        # 1. Create
        archive = sm.create_snapshot(self.test_dir, self.dest_archive)
        self.assertTrue(os.path.exists(archive))
        
        # 2. Checksum
        ch = sm.calculate_checksum(archive)
        self.assertTrue(sm.verify_checksum(archive, ch))

        # 3. Restore
        rm = RestoreManager()
        ok, msg = rm.restore_storage(archive, "test_ops_restored")
        self.assertTrue(ok)
        self.assertTrue(os.path.exists("test_ops_restored"))
