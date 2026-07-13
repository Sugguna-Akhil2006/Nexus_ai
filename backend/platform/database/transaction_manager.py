"""Transaction manager supporting ACID commits and rollbacks."""

from typing import Any, Generator
from contextlib import contextmanager

from backend.platform.database.connection_pool import ConnectionPool


class TransactionManager:
    """Manages transactional boundaries using a connection pool context."""

    def __init__(self, pool: ConnectionPool) -> None:
        """Initializes the transaction manager.

        Args:
            pool: Database connection pool.
        """
        self.pool = pool

    @contextmanager
    def transaction(self) -> Generator[Any, None, None]:
        """Context manager yielding a transactional database connection.

        Commits on completion; rolls back if an exception occurs.
        """
        conn = self.pool.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            self.pool.release_connection(conn)
