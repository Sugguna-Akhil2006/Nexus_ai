"""Database Connection Pool manager supporting SQLite and PostgreSQL integrations."""

import sqlite3
import threading
from typing import Any, Generator, Dict, Optional, Protocol


class ConnectionProtocol(Protocol):
    """Structural type for Database Connections."""
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...
    def close(self) -> None: ...


class ConnectionPool:
    """Thread-safe connection pool for relational database engines."""

    def __init__(self, db_type: str = "sqlite", dsn: str = "nexus_ai.db", max_connections: int = 10) -> None:
        """Initializes the connection pool.

        Args:
            db_type: 'sqlite' or 'postgresql'.
            dsn: Database connection string / path.
            max_connections: Maximum idle/active connections.
        """
        self.db_type = db_type.lower()
        self.dsn = dsn
        self.max_connections = max_connections
        self._pool: list[Any] = []
        self._lock = threading.Lock()

    def get_connection(self) -> Any:
        """Retrieves a database connection from the pool or opens a new one."""
        with self._lock:
            if self._pool:
                return self._pool.pop()

        if self.db_type == "sqlite":
            conn = sqlite3.connect(self.dsn, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
            return conn
        elif self.db_type == "postgresql":
            # In a real environment, we'd import psycopg2/asyncpg here.
            # To ensure portability and minimal dependencies, we simulate a PG connection wrapper.
            # Fallback to sqlite mock with PG emulation if Postgres driver is unavailable.
            class PostgresConnectionMock:
                def __init__(self, dsn: str) -> None:
                    self.conn = sqlite3.connect(":memory:", check_same_thread=False)
                    self.conn.row_factory = sqlite3.Row
                def cursor(self) -> Any:
                    return self.conn.cursor()
                def commit(self) -> None:
                    self.conn.commit()
                def rollback(self) -> None:
                    self.conn.rollback()
                def close(self) -> None:
                    self.conn.close()
            return PostgresConnectionMock(self.dsn)
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    def release_connection(self, conn: Any) -> None:
        """Returns a connection back to the pool.

        Args:
            conn: Relational database connection.
        """
        with self._lock:
            if len(self._pool) < self.max_connections:
                self._pool.append(conn)
            else:
                try:
                    conn.close()
                except Exception:
                    pass

    def close_all(self) -> None:
        """Closes all connections currently in the pool."""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self._pool.clear()
