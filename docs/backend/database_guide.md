# Database Guide - Nexus AI

This guide documents the schema layout, connection pooling, migrations, and database recovery strategies.

## Relational Architecture

The default local engine is SQLite (`nexus_ai.db`), running in thread-safe WAL mode. In clustered production environments, Postgres is the recommended backend.

### Database Recovery

To recover the database from a backup file, execute:

```python
from backend.platform.database.connection_pool import ConnectionPool
from backend.platform.database.backup_manager import BackupManager

pool = ConnectionPool(db_type="sqlite", dsn="nexus_ai.db")
backup_mgr = BackupManager(pool)

# Restores database state from snapshot
backup_mgr.restore_backup("nexus_snapshot.db")
```
