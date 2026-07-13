"""Generic repository pattern module representing database entities access layer."""

from typing import List, Dict, Any, Optional
from backend.platform.database.connection_pool import ConnectionPool


class BaseRepository:
    """Generic CRUD SQL executor class for domain objects."""

    def __init__(self, pool: ConnectionPool, table_name: str) -> None:
        """Initializes the repository.

        Args:
            pool: Connection pool.
            table_name: SQL table name.
        """
        self.pool = pool
        self.table_name = table_name

    def find_by_id(self, entity_id: Any, id_column: str = "id") -> Optional[Dict[str, Any]]:
        """Retrieves a single record by its identifier column."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        query = f"SELECT * FROM {self.table_name} WHERE {id_column} = ?"
        try:
            cursor.execute(query, (entity_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            self.pool.release_connection(conn)

    def list_all(self) -> List[Dict[str, Any]]:
        """Lists all rows in the database table."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        query = f"SELECT * FROM {self.table_name}"
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            self.pool.release_connection(conn)

    def insert(self, data: Dict[str, Any]) -> bool:
        """Inserts a new record in the table."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        try:
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.release_connection(conn)

    def update(self, entity_id: Any, data: Dict[str, Any], id_column: str = "id") -> bool:
        """Updates fields of a record matching key criteria."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clause} WHERE {id_column} = ?"
        params = list(data.values()) + [entity_id]
        try:
            cursor.execute(query, tuple(params))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.release_connection(conn)

    def delete(self, entity_id: Any, id_column: str = "id") -> bool:
        """Removes a row from the database table."""
        conn = self.pool.get_connection()
        cursor = conn.cursor()
        query = f"DELETE FROM {self.table_name} WHERE {id_column} = ?"
        try:
            cursor.execute(query, (entity_id,))
            conn.commit()
            return cursor.rowcount > 0
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.release_connection(conn)
