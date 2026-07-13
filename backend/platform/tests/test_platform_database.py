"""Unit tests for Platform Database module."""

import os
import sqlite3
import unittest

from backend.platform.database.connection_pool import ConnectionPool
from backend.platform.database.transaction_manager import TransactionManager
from backend.platform.database.repository import BaseRepository
from backend.platform.database.migration_manager import MigrationManager
from backend.platform.database.backup_manager import BackupManager


class TestPlatformDatabase(unittest.TestCase):
    """Test suite covering connections, repositories, migrations, and database backups."""

    def setUp(self) -> None:
        self.pool = ConnectionPool(db_type="sqlite", dsn=":memory:")
        self.tx = TransactionManager(self.pool)

    def tearDown(self) -> None:
        self.pool.close_all()

    def test_connection_pool_retrieval(self) -> None:
        """Verifies connection acquisition and releasing cycles."""
        conn = self.pool.get_connection()
        self.assertIsNotNone(conn)
        self.pool.release_connection(conn)

    def test_repository_crud(self) -> None:
        """Verifies CRUD operations inside repository abstraction layer."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
        conn.commit()
        self.pool.release_connection(conn)

        repo = BaseRepository(self.pool, "test_table")
        
        # Insert
        repo.insert({"id": 1, "name": "Nexus"})
        entity = repo.find_by_id(1)
        self.assertEqual(entity["name"], "Nexus")

        # Update
        repo.update(1, {"name": "Nexus Platform"})
        entity = repo.find_by_id(1)
        self.assertEqual(entity["name"], "Nexus Platform")

        # Delete
        repo.delete(1)
        self.assertIsNone(repo.find_by_id(1))

    def test_transaction_rollback(self) -> None:
        """Verifies transactions rollback states on encountered errors."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE tx_table (id INTEGER PRIMARY KEY, val TEXT)")
        conn.commit()
        self.pool.release_connection(conn)

        try:
            with self.tx.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO tx_table VALUES (1, 'initial')")
                # Intentionally fail
                raise ValueError("Force transaction fail")
        except ValueError:
            pass

        # Verify no insertions occurred
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tx_table")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        self.pool.release_connection(conn)

    def test_migration_manager(self) -> None:
        """Verifies migration parsing and schema auditing tracking."""
        mgr = MigrationManager(self.pool)
        sql = ["CREATE TABLE m_table (id INTEGER PRIMARY KEY)"]
        
        # Apply migration
        self.assertTrue(mgr.apply_migration(1, "Create m_table", sql))
        self.assertIn(1, mgr.get_applied_versions())

    def test_backup_manager(self) -> None:
        """Verifies SQLite hot backups and restorations."""
        db_file = "test_nexus_backup.db"
        backup_pool = ConnectionPool(db_type="sqlite", dsn=db_file)
        
        conn = backup_pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE bk_table (id INTEGER PRIMARY KEY)")
        conn.commit()
        backup_pool.release_connection(conn)

        backup_mgr = BackupManager(backup_pool, default_backup_dir="test_backups")
        backup_file = "nexus_snapshot.db"
        
        try:
            backup_path = backup_mgr.create_backup(backup_file)
            self.assertTrue(os.path.exists(backup_path))
            
            # Restore backup verification
            self.assertTrue(backup_mgr.restore_backup(backup_file))
        finally:
            backup_pool.close_all()
            if os.path.exists(db_file):
                os.remove(db_file)
            if os.path.exists("test_backups"):
                import shutil
                shutil.rmtree("test_backups")
