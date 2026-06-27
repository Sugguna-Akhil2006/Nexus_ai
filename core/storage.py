from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import dataclasses
from datetime import datetime
import threading
from typing import Any, Dict, List, Optional
import uuid

from core.event import Event, EventBus, EventType
from core.exceptions import NexusException
from core.logger import StructuredLogger


class StorageError(NexusException):
    """Base exception for all storage-related errors."""
    pass


class StorageValidationError(StorageError):
    """Raised when record properties, namespaces or query inputs are invalid."""
    pass


class StorageNotFoundError(StorageError):
    """Raised when the specified record is not found in the storage."""
    pass


class TransactionError(StorageError):
    """Raised when transaction state operations fail."""
    pass


@dataclass(frozen=True)
class StorageRecord:
    """Immutable model representing a stored data record.

    Attributes:
        id: Unique identifier for the record.
        namespace: The logical namespace/bucket this record belongs to.
        payload: Dict containing the user payload.
        metadata: Dict containing additional queryable metadata.
        version: Version counter for optimistic concurrency checking.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
    """
    id: str
    namespace: str
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class StorageQuery:
    """Encapsulates filter matching, sorting constraints, and pagination limits.

    Attributes:
        filters: Key-value filters to match payload or metadata values.
        sorting: Key-value map defining field and order ("ASC" or "DESC").
        limit: Max records to return.
        offset: Records starting offset count.
    """
    filters: Dict[str, Any] = field(default_factory=dict)
    sorting: Dict[str, str] = field(default_factory=dict)
    limit: Optional[int] = None
    offset: Optional[int] = None


class Transaction(ABC):
    """Abstract interface defining standard database transaction capabilities."""

    @abstractmethod
    def commit(self) -> None:
        """Commits staging data modifications to the persistent target database."""
        pass

    @abstractmethod
    def rollback(self) -> None:
        """Aborts staging data modifications, reverting context state."""
        pass

    def __enter__(self) -> "Transaction":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()


class StorageProvider(ABC):
    """Abstract base class establishing generic storage capabilities interface."""

    @abstractmethod
    def create(self, record: StorageRecord) -> None:
        """Saves a new StorageRecord.

        Args:
            record: The StorageRecord.
        """
        pass

    @abstractmethod
    def read(self, namespace: str, record_id: str) -> StorageRecord:
        """Reads a StorageRecord by ID.

        Args:
            namespace: The logical namespace.
            record_id: Unique record ID.
        """
        pass

    @abstractmethod
    def update(self, record: StorageRecord) -> None:
        """Updates an existing record.

        Args:
            record: The updated record.
        """
        pass

    @abstractmethod
    def delete(self, namespace: str, record_id: str) -> None:
        """Deletes a record.

        Args:
            namespace: The logical namespace.
            record_id: Unique record ID.
        """
        pass

    @abstractmethod
    def exists(self, namespace: str, record_id: str) -> bool:
        """Checks if a record exists.

        Args:
            namespace: The logical namespace.
            record_id: Unique record ID.
        """
        pass

    @abstractmethod
    def list(self, namespace: str) -> List[StorageRecord]:
        """Lists all records in a namespace.

        Args:
            namespace: The logical namespace.
        """
        pass

    @abstractmethod
    def query(self, namespace: str, query_def: StorageQuery) -> List[StorageRecord]:
        """Queries records in a namespace matching filter/pagination bounds.

        Args:
            namespace: The logical namespace.
            query_def: The StorageQuery definition.
        """
        pass

    @abstractmethod
    def begin_transaction(self) -> Transaction:
        """Starts a transaction context."""
        pass


class MemoryTransaction(Transaction):
    """Staged isolation container for in-memory transactional scopes."""

    def __init__(self, provider: "MemoryStorageProvider") -> None:
        self._provider = provider
        self._committed = False
        self._rolled_back = False
        with provider._lock:
            # Staging isolation copy
            self._staging = {
                ns: {rid: rec for rid, rec in records.items()}
                for ns, records in provider._store.items()
            }

    def commit(self) -> None:
        """Applies staging mutations back to the main memory store."""
        if self._committed or self._rolled_back:
            return
        with self._provider._lock:
            self._provider._store = self._staging
            self._committed = True
            # Clear thread-local active transaction
            if getattr(self._provider._local_tx, "active_tx", None) is self:
                self._provider._local_tx.active_tx = None

        self._provider._publish_event("storage.transaction.committed", transaction_id=id(self))

    def rollback(self) -> None:
        """Aborts and discards all staging modifications."""
        if self._committed or self._rolled_back:
            return
        self._rolled_back = True
        with self._provider._lock:
            # Clear thread-local active transaction
            if getattr(self._provider._local_tx, "active_tx", None) is self:
                self._provider._local_tx.active_tx = None

        self._provider._publish_event("storage.transaction.rolledback", transaction_id=id(self))


class MemoryStorageProvider(StorageProvider):
    """Thread-safe Singleton in-memory persistence provider."""
    _instance: Optional["MemoryStorageProvider"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "MemoryStorageProvider":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self.logger = StructuredLogger()
            self.event_bus = EventBus()
            self._store: Dict[str, Dict[str, StorageRecord]] = {}
            self._local_tx = threading.local()
            self._lock: threading.RLock = threading.RLock()
            self._initialized = True

    def _get_target_store(self) -> Dict[str, Dict[str, StorageRecord]]:
        tx = getattr(self._local_tx, "active_tx", None)
        if tx and not tx._rolled_back and not tx._committed:
            return tx._staging
        return self._store

    def create(self, record: StorageRecord) -> None:
        """Saves a new record into memory storage.

        Args:
            record: The StorageRecord.

        Raises:
            StorageValidationError: On missing parameters or duplicate key ID.
        """
        if not record or not record.id or not str(record.id).strip():
            raise StorageValidationError("Record must contain a valid ID.")
        if not record.namespace or not str(record.namespace).strip():
            raise StorageValidationError("Record must specify a valid namespace.")

        self.logger.info(f"Storage create started for ID: {record.id} in namespace: {record.namespace}")

        with self._lock:
            store = self._get_target_store()
            if record.namespace not in store:
                store[record.namespace] = {}

            if record.id in store[record.namespace]:
                raise StorageValidationError(
                    f"Record with ID '{record.id}' already exists in namespace '{record.namespace}'."
                )

            store[record.namespace][record.id] = record

        self._publish_event("storage.created", record.namespace, record.id)
        self.logger.info(f"Successful storage create. ID: {record.id}")

    def read(self, namespace: str, record_id: str) -> StorageRecord:
        """Retrieves record by ID.

        Args:
            namespace: The logical namespace.
            record_id: Unique record ID.

        Returns:
            StorageRecord: The retrieved record.

        Raises:
            StorageNotFoundError: If record is missing.
        """
        if not namespace or not record_id:
            raise StorageValidationError("namespace and record_id must be provided.")

        with self._lock:
            store = self._get_target_store()
            records = store.get(namespace, {})
            if record_id not in records:
                raise StorageNotFoundError(
                    f"Record '{record_id}' not found in namespace '{namespace}'."
                )
            return records[record_id]

    def update(self, record: StorageRecord) -> None:
        """Updates record details and increments the version counter.

        Args:
            record: The target updated record definition.

        Raises:
            StorageNotFoundError: If record doesn't exist.
        """
        if not record or not record.id or not record.namespace:
            raise StorageValidationError("Invalid record details for update.")

        self.logger.info(f"Storage update started for ID: {record.id} in namespace: {record.namespace}")

        with self._lock:
            store = self._get_target_store()
            records = store.get(record.namespace, {})
            if record.id not in records:
                raise StorageNotFoundError(
                    f"Record '{record.id}' not found in namespace '{record.namespace}'."
                )

            existing = records[record.id]
            updated_record = dataclasses.replace(
                record,
                version=existing.version + 1,
                updated_at=datetime.utcnow()
            )
            records[record.id] = updated_record

        self._publish_event("storage.updated", record.namespace, record.id)
        self.logger.info(f"Successful storage update. ID: {record.id}")

    def delete(self, namespace: str, record_id: str) -> None:
        """Removes a record from the database storage.

        Args:
            namespace: The logical namespace.
            record_id: Unique record ID.

        Raises:
            StorageNotFoundError: If record is missing.
        """
        if not namespace or not record_id:
            raise StorageValidationError("namespace and record_id must be provided.")

        self.logger.info(f"Storage delete started for ID: {record_id} in namespace: {namespace}")

        with self._lock:
            store = self._get_target_store()
            records = store.get(namespace, {})
            if record_id not in records:
                raise StorageNotFoundError(
                    f"Record '{record_id}' not found in namespace '{namespace}'."
                )
            del records[record_id]

        self._publish_event("storage.deleted", namespace, record_id)
        self.logger.info(f"Successful storage delete. ID: {record_id}")

    def exists(self, namespace: str, record_id: str) -> bool:
        """Checks if a record is present in storage.

        Args:
            namespace: Logical namespace mapping.
            record_id: Unique record ID identifier.

        Returns:
            bool: True if present, False otherwise.
        """
        with self._lock:
            store = self._get_target_store()
            return record_id in store.get(namespace, {})

    def list(self, namespace: str) -> List[StorageRecord]:
        """Lists all records within a namespace logically.

        Args:
            namespace: Logical namespace mapping.

        Returns:
            List[StorageRecord]: StorageRecords present.
        """
        with self._lock:
            store = self._get_target_store()
            return list(store.get(namespace, {}).values())

    def query(self, namespace: str, query_def: StorageQuery) -> List[StorageRecord]:
        """Executes a structured query evaluating payload filters.

        Args:
            namespace: The logical namespace.
            query_def: Search query bounds criteria definition.

        Returns:
            List[StorageRecord]: Match storage records.
        """
        if not namespace or not query_def:
            raise StorageValidationError("namespace and query_def must be provided.")

        self.logger.info(f"Storage query execution started for namespace: {namespace}")

        with self._lock:
            records = self.list(namespace)

        # Filters match logic
        results = []
        for rec in records:
            matched = True
            for k, v in query_def.filters.items():
                if k in rec.payload:
                    if rec.payload[k] != v:
                        matched = False
                        break
                elif k in rec.metadata:
                    if rec.metadata[k] != v:
                        matched = False
                        break
                else:
                    matched = False
                    break
            if matched:
                results.append(rec)

        # Sorting logic
        if query_def.sorting:
            for sort_field, sort_order in query_def.sorting.items():
                reverse = (sort_order.upper() == "DESC")

                def sort_key(r: StorageRecord) -> Any:
                    if hasattr(r, sort_field):
                        return getattr(r, sort_field)
                    if sort_field in r.payload:
                        return r.payload[sort_field]
                    if sort_field in r.metadata:
                        return r.metadata[sort_field]
                    return ""

                results.sort(key=sort_key, reverse=reverse)

        # Offsets / limits pagination logic
        if query_def.offset is not None:
            results = results[query_def.offset:]
        if query_def.limit is not None:
            results = results[:query_def.limit]

        return results

    def begin_transaction(self) -> Transaction:
        """Initializes a new memory staged transaction context manager.

        Returns:
            Transaction: The active transaction context.
        """
        with self._lock:
            tx = MemoryTransaction(self)
            self._local_tx.active_tx = tx
            self._publish_event("storage.transaction.started", transaction_id=id(tx))
            self.logger.info(f"Staged memory transaction started. ID: {id(tx)}")
            return tx

    def _publish_event(self, event_name: str, namespace: Optional[str] = None, record_id: Optional[str] = None, **kwargs: Any) -> None:
        payload = {"event_name": event_name, **kwargs}
        if namespace:
            payload["namespace"] = namespace
        if record_id:
            payload["record_id"] = record_id

        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="StorageLayer",
            payload=payload
        )
        self.event_bus.publish(event)
