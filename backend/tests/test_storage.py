from datetime import datetime
import threading
from typing import List
import unittest

from backend.runtime.event import Event, EventBus, EventType
from backend.interfaces.storage import (
    MemoryStorageProvider,
    StorageQuery,
    StorageRecord,
    StorageNotFoundError,
    StorageValidationError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestStorage(unittest.TestCase):
    """Suite of tests covering the Storage Layer abstraction and implementation."""

    def setUp(self) -> None:
        self.provider = MemoryStorageProvider()
        with self.provider._lock:
            self.provider._store.clear()
            # Clear active transaction if any
            if hasattr(self.provider._local_tx, "active_tx"):
                self.provider._local_tx.active_tx = None
        self.event_bus = EventBus()
        self.event_bus.clear()

    def test_singleton(self) -> None:
        """Verifies that MemoryStorageProvider behaves as a singleton."""
        provider2 = MemoryStorageProvider()
        self.assertIs(self.provider, provider2)

    def test_crud_lifecycle(self) -> None:
        """Verifies create, read, update, delete, and exists workflow."""
        record = StorageRecord(
            id="rec_01",
            namespace="user_profiles",
            payload={"name": "Alice", "role": "developer"},
            metadata={"source": "api"}
        )

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Create
        self.provider.create(record)
        self.assertTrue(self.provider.exists("user_profiles", "rec_01"))

        # Read
        retrieved = self.provider.read("user_profiles", "rec_01")
        self.assertEqual(retrieved.payload["name"], "Alice")
        self.assertEqual(retrieved.version, 1)

        # Update
        updated_record = StorageRecord(
            id="rec_01",
            namespace="user_profiles",
            payload={"name": "Alice", "role": "senior developer"},
            metadata={"source": "api"}
        )
        self.provider.update(updated_record)

        # Read after update
        retrieved_updated = self.provider.read("user_profiles", "rec_01")
        self.assertEqual(retrieved_updated.payload["role"], "senior developer")
        self.assertEqual(retrieved_updated.version, 2)

        # Delete
        self.provider.delete("user_profiles", "rec_01")
        self.assertFalse(self.provider.exists("user_profiles", "rec_01"))

        with self.assertRaises(StorageNotFoundError):
            self.provider.read("user_profiles", "rec_01")

        # Verify Event Bus triggers
        self.event_bus.dispatch_all()
        created_events = [e for e in receiver.events if e.payload["event_name"] == "storage.created"]
        updated_events = [e for e in receiver.events if e.payload["event_name"] == "storage.updated"]
        deleted_events = [e for e in receiver.events if e.payload["event_name"] == "storage.deleted"]

        self.assertEqual(len(created_events), 1)
        self.assertEqual(len(updated_events), 1)
        self.assertEqual(len(deleted_events), 1)

    def test_validation_constraints(self) -> None:
        """Verifies duplicate keys or invalid arguments trigger errors."""
        # Empty record fields
        with self.assertRaises(StorageValidationError):
            self.provider.create(StorageRecord(id="", namespace="ns", payload={}))

        with self.assertRaises(StorageValidationError):
            self.provider.create(StorageRecord(id="rec", namespace="", payload={}))

        # Duplicate ID
        rec = StorageRecord(id="rec1", namespace="ns1", payload={"data": 1})
        self.provider.create(rec)
        with self.assertRaises(StorageValidationError):
            self.provider.create(rec)

        # Missing read
        with self.assertRaises(StorageNotFoundError):
            self.provider.read("ns1", "non_existent")

        # Missing update
        with self.assertRaises(StorageNotFoundError):
            self.provider.update(StorageRecord(id="non_existent", namespace="ns1", payload={}))

        # Missing delete
        with self.assertRaises(StorageNotFoundError):
            self.provider.delete("ns1", "non_existent")

    def test_transaction_commit(self) -> None:
        """Verifies transaction staging isolations commit correctly."""
        record = StorageRecord(id="tx_rec", namespace="tx_ns", payload={"value": "staged"})

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Start transaction context
        tx = self.provider.begin_transaction()
        self.provider.create(record)

        # Must not be visible in main store yet
        self.assertFalse("tx_rec" in self.provider._store.get("tx_ns", {}))

        # Commit
        tx.commit()

        # Must be present now
        self.assertTrue(self.provider.exists("tx_ns", "tx_rec"))
        self.assertEqual(self.provider.read("tx_ns", "tx_rec").payload["value"], "staged")

        self.event_bus.dispatch_all()
        commit_events = [e for e in receiver.events if e.payload["event_name"] == "storage.transaction.committed"]
        self.assertEqual(len(commit_events), 1)

    def test_transaction_rollback(self) -> None:
        """Verifies rolled back transactions discard staged alterations."""
        record = StorageRecord(id="tx_rec", namespace="tx_ns", payload={"value": "staged"})

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        tx = self.provider.begin_transaction()
        self.provider.create(record)
        # Verify it is not visible in main store while transaction is active
        self.assertFalse("tx_rec" in self.provider._store.get("tx_ns", {}))
        tx.rollback()

        self.assertFalse(self.provider.exists("tx_ns", "tx_rec"))

        self.event_bus.dispatch_all()
        rollback_events = [e for e in receiver.events if e.payload["event_name"] == "storage.transaction.rolledback"]
        self.assertEqual(len(rollback_events), 1)

    def test_transaction_context_manager(self) -> None:
        """Verifies context manager automatic rollback on error or commit on success."""
        # Success context managers auto-commits
        with self.provider.begin_transaction():
            self.provider.create(StorageRecord(id="c_rec", namespace="c_ns", payload={"a": 1}))

        self.assertTrue(self.provider.exists("c_ns", "c_rec"))

        # Exception context manager auto-rolls back
        try:
            with self.provider.begin_transaction():
                self.provider.create(StorageRecord(id="c_rec_err", namespace="c_ns", payload={"a": 2}))
                self.assertFalse("c_rec_err" in self.provider._store.get("c_ns", {}))
                raise ValueError("Abort this context run")
        except ValueError:
            pass

        self.assertFalse(self.provider.exists("c_ns", "c_rec_err"))

    def test_queries_filtering_sorting_pagination(self) -> None:
        """Verifies structured querying, payload filtering, offsets, limits, and sorts."""
        r1 = StorageRecord(id="1", namespace="users", payload={"age": 25, "name": "Alice"}, metadata={"tag": "dev"})
        r2 = StorageRecord(id="2", namespace="users", payload={"age": 35, "name": "Bob"}, metadata={"tag": "manager"})
        r3 = StorageRecord(id="3", namespace="users", payload={"age": 30, "name": "Charlie"}, metadata={"tag": "dev"})

        self.provider.create(r1)
        self.provider.create(r2)
        self.provider.create(r3)

        # Query filters matches metadata and payload
        q_filter = StorageQuery(filters={"tag": "dev"})
        results = self.provider.query("users", q_filter)
        self.assertEqual(len(results), 2)
        self.assertEqual({r.id for r in results}, {"1", "3"})

        # Sorting check (age descending)
        q_sort = StorageQuery(sorting={"age": "DESC"})
        results_sorted = self.provider.query("users", q_sort)
        self.assertEqual(results_sorted[0].id, "2")  # age 35
        self.assertEqual(results_sorted[1].id, "3")  # age 30
        self.assertEqual(results_sorted[2].id, "1")  # age 25

        # Pagination offsets and limits
        q_page = StorageQuery(sorting={"age": "ASC"}, limit=2, offset=1)
        results_page = self.provider.query("users", q_page)
        self.assertEqual(len(results_page), 2)
        self.assertEqual(results_page[0].id, "3")  # age 30
        self.assertEqual(results_page[1].id, "2")  # age 35

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent threads writing records in different namespaces safely."""
        num_threads = 10
        records_per_thread = 20

        def worker(thread_idx: int) -> None:
            for i in range(records_per_thread):
                record = StorageRecord(
                    id=f"rec_{i}",
                    namespace=f"ns_{thread_idx}",
                    payload={"thread": thread_idx, "index": i}
                )
                self.provider.create(record)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check total record list size
        for idx in range(num_threads):
            recs = self.provider.list(f"ns_{idx}")
            self.assertEqual(len(recs), records_per_thread)


if __name__ == "__main__":
    unittest.main()
