"""Connector Manager facade coordinating all database connection, sync and health operations."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.connectors.models import ConnectorConfig, ConnectionHealth, SyncJob
from backend.connectors.connector_registry import ConnectorRegistry
from backend.connectors.credential_manager import CredentialManager
from backend.connectors.rate_limiter import ConnectorRateLimiter
from backend.connectors.connection_pool import ConnectionPool
from backend.connectors.sync_engine import SyncEngine
from backend.connectors.connector_scheduler import ConnectorScheduler
from backend.connectors.connector_health import ConnectorHealthMonitor
from backend.connectors.event_adapter import ConnectorEventAdapter


class ConnectorManager:
    """Administrative unified facade coordinating the Universal Connector Framework operations."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self.registry = ConnectorRegistry()
        self.credential_mgr = CredentialManager()
        self.pool = ConnectionPool(self.registry)
        self.sync_engine = SyncEngine(self.pool)
        self.scheduler = ConnectorScheduler(self.sync_engine)
        self.health_monitor = ConnectorHealthMonitor(self.pool)
        self.event_adapter = ConnectorEventAdapter()
        self.rate_limiter = ConnectorRateLimiter(60)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_connectors (
                connector_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                connector_type TEXT NOT NULL,
                name TEXT NOT NULL,
                encrypted_auth TEXT NOT NULL,
                metadata TEXT NOT NULL,
                is_active INTEGER NOT NULL,
                last_sync TEXT
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def configure_connector(self, config: ConnectorConfig) -> None:
        """Saves a connector configuration details, encrypting authentication tokens."""
        encrypted_auth = self.credential_mgr.encrypt_credentials(config.auth_data)
        
        with self._lock:
            conn = self._db._get_connection()
            try:
                import json
                conn.execute("""
                INSERT INTO platform_connectors (
                    connector_id, workspace_id, connector_type, name, encrypted_auth, metadata, is_active, last_sync
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(connector_id) DO UPDATE SET
                    name=excluded.name,
                    encrypted_auth=excluded.encrypted_auth,
                    metadata=excluded.metadata,
                    is_active=excluded.is_active,
                    last_sync=excluded.last_sync
                """, (
                    config.connector_id,
                    config.workspace_id,
                    config.connector_type,
                    config.name,
                    encrypted_auth,
                    json.dumps(config.metadata),
                    1 if config.is_active else 0,
                    config.last_sync_timestamp
                ))
                conn.commit()
            finally:
                conn.close()

            # Emit connected event
            self.event_adapter.publish_connection_event("connector.connected", config.connector_id, config.connector_type)

    def delete_connector(self, connector_id: str) -> None:
        """Removes connector configuration details."""
        config = self.get_connector(connector_id)
        if config:
            with self._lock:
                conn = self._db._get_connection()
                try:
                    conn.execute("DELETE FROM platform_connectors WHERE connector_id = ?", (connector_id,))
                    conn.commit()
                finally:
                    conn.close()
            
            # Emit disconnected event
            self.event_adapter.publish_connection_event("connector.disconnected", connector_id, config.connector_type)
            self.pool.remove_connection(connector_id)
            self.scheduler.unschedule_connector(connector_id)

    def get_connector(self, connector_id: str) -> Optional[ConnectorConfig]:
        conn = self._db._get_connection()
        try:
            r = conn.execute("SELECT * FROM platform_connectors WHERE connector_id = ?", (connector_id,)).fetchone()
            if r:
                import json
                auth_data = self.credential_mgr.decrypt_credentials(r["encrypted_auth"])
                return ConnectorConfig(
                    connector_id=r["connector_id"],
                    workspace_id=r["workspace_id"],
                    connector_type=r["connector_type"],
                    name=r["name"],
                    auth_data=auth_data,
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                    is_active=bool(r["is_active"]),
                    last_sync_timestamp=r["last_sync"]
                )
            return None
        finally:
            conn.close()

    def list_connectors(self) -> List[ConnectorConfig]:
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM platform_connectors").fetchall()
            import json
            configs = []
            for r in rows:
                auth_data = self.credential_mgr.decrypt_credentials(r["encrypted_auth"])
                configs.append(ConnectorConfig(
                    connector_id=r["connector_id"],
                    workspace_id=r["workspace_id"],
                    connector_type=r["connector_type"],
                    name=r["name"],
                    auth_data=auth_data,
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                    is_active=bool(r["is_active"]),
                    last_sync_timestamp=r["last_sync"]
                ))
            return configs
        finally:
            conn.close()

    def sync_connector(self, connector_id: str) -> Optional[SyncJob]:
        """Triggers dynamic synchronization using the sync engine."""
        config = self.get_connector(connector_id)
        if not config or not config.is_active:
            raise ValueError(f"Active connector '{connector_id}' not found.")

        # Rate limiting check
        if not self.rate_limiter.consume():
            raise PermissionError("Connector API rate limits exceeded. Throttling active.")

        job = self.sync_engine.trigger_sync(config)
        
        # Save updated last sync timestamp
        if job.status == "completed":
            config.last_sync_timestamp = job.end_time.isoformat()
            self.configure_connector(config)

        return job

    def clear(self) -> None:
        """Clears connectors DB for testing."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM platform_connectors")
                conn.commit()
            finally:
                conn.close()
            self.pool.clear()
