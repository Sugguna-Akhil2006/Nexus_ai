from datetime import datetime
import threading
from typing import Any, Dict, List
import unittest
import uuid

from core.event import Event, EventBus, EventType
from core.vector import (
    CollectionInfo,
    CollectionNotFoundError,
    CosineSimilarityStrategy,
    DotProductSimilarityStrategy,
    EuclideanSimilarityStrategy,
    FilterEngine,
    ManhattanSimilarityStrategy,
    MemoryVectorProvider,
    ProviderNotFoundError,
    SearchRequest,
    SearchResult,
    VectorError,
    VectorRecord,
    VectorRegistry,
    VectorValidationError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestVectorSystem(unittest.TestCase):
    """Suite of tests covering the Vector Engine and Registry system."""

    def setUp(self) -> None:
        self.registry = VectorRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.provider = MemoryVectorProvider("memory_test")

    def test_singleton(self) -> None:
        """Verifies that VectorRegistry behaves as a singleton."""
        registry2 = VectorRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration_validation(self) -> None:
        """Verifies registrations enforce uniqueness constraints and validate fields."""
        # Register provider
        self.registry.register_provider("mem_p", self.provider)
        self.assertIn("mem_p", self.registry.list_providers())

        # Duplicate registration raises error
        with self.assertRaises(VectorValidationError):
            self.registry.register_provider("mem_p", self.provider)

        # Unregistering provider
        self.registry.unregister_provider("mem_p")
        self.assertNotIn("mem_p", self.registry.list_providers())

        with self.assertRaises(ProviderNotFoundError):
            self.registry.get_provider("mem_p")

    def test_similarity_strategies(self) -> None:
        """Verifies distance metric calculation strategies."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [0.0, 1.0, 0.0]
        v3 = [1.0, 0.0, 0.0]

        # Cosine Similarity
        cosine = CosineSimilarityStrategy()
        self.assertAlmostEqual(cosine.calculate(v1, v3), 1.0)
        self.assertAlmostEqual(cosine.calculate(v1, v2), 0.0)

        # Dot Product
        dot = DotProductSimilarityStrategy()
        self.assertEqual(dot.calculate(v1, v3), 1.0)
        self.assertEqual(dot.calculate(v1, v2), 0.0)

        # Euclidean Similarity (d=sqrt(2) approx 1.414, similarity=1/(1+1.414)=0.414)
        euclidean = EuclideanSimilarityStrategy()
        self.assertAlmostEqual(euclidean.calculate(v1, v1), 1.0)
        self.assertTrue(0.4 < euclidean.calculate(v1, v2) < 0.42)

        # Manhattan Similarity (d=2, similarity=1/(1+2)=0.333)
        manhattan = ManhattanSimilarityStrategy()
        self.assertAlmostEqual(manhattan.calculate(v1, v1), 1.0)
        self.assertAlmostEqual(manhattan.calculate(v1, v2), 1.0 / 3.0)

    def test_filter_engine(self) -> None:
        """Verifies recursive Query Filter Engine matches evaluation metadata properties."""
        meta = {
            "category": "science",
            "rating": 4.5,
            "tags": ["physics", "ai"],
            "published": True
        }

        # Equality
        self.assertTrue(FilterEngine.matches(meta, {"category": "science"}))
        self.assertFalse(FilterEngine.matches(meta, {"category": "math"}))

        # Comparison operators
        self.assertTrue(FilterEngine.matches(meta, {"rating": {"$gt": 4.0}}))
        self.assertTrue(FilterEngine.matches(meta, {"rating": {"$lte": 4.5}}))
        self.assertFalse(FilterEngine.matches(meta, {"rating": {"$lt": 4.5}}))

        # Contains
        self.assertTrue(FilterEngine.matches(meta, {"tags": {"$contains": "physics"}}))
        self.assertFalse(FilterEngine.matches(meta, {"tags": {"$contains": "history"}}))

        # Logical AND
        self.assertTrue(FilterEngine.matches(meta, {"$and": [{"category": "science"}, {"rating": {"$gt": 4.0}}]}))
        self.assertFalse(FilterEngine.matches(meta, {"$and": [{"category": "science"}, {"rating": {"$lt": 4.0}}]}))

        # Logical OR
        self.assertTrue(FilterEngine.matches(meta, {"$or": [{"category": "math"}, {"rating": {"$gt": 4.0}}]}))
        self.assertFalse(FilterEngine.matches(meta, {"$or": [{"category": "math"}, {"rating": {"$lt": 4.0}}]}))

    def test_provider_indexing_lifecycle_and_dimensions_validation(self) -> None:
        """Verifies create_collection, dimensions matches, insert/update/delete, and errors."""
        info = CollectionInfo(
            collection_id="col1",
            name="Collection One",
            dimensions=3,
            similarity_metric="cosine"
        )
        self.provider.create_collection(info)
        self.assertIn(info, self.provider.list_collections())

        # Duplicate collections raise error
        with self.assertRaises(VectorValidationError):
            self.provider.create_collection(info)

        # Dimension mismatch raises error on insert
        bad_rec = VectorRecord(
            vector_id="v1",
            collection="col1",
            embedding=[1.0, 2.0]  # only 2 dimensions
        )
        with self.assertRaises(VectorValidationError):
            self.provider.insert([bad_rec])

        # Successful insert
        r1 = VectorRecord(
            vector_id="v1",
            collection="col1",
            embedding=[1.0, 0.0, 0.0],
            metadata={"category": "ai"}
        )
        r2 = VectorRecord(
            vector_id="v2",
            collection="col1",
            embedding=[0.0, 1.0, 0.0],
            metadata={"category": "physics"}
        )
        self.provider.insert([r1, r2])

        # Duplicate ID insert raises error
        with self.assertRaises(VectorValidationError):
            self.provider.insert([r1])

        # Successful update
        r1_mod = VectorRecord(
            vector_id="v1",
            collection="col1",
            embedding=[0.8, 0.6, 0.0],  # norm = 1.0
            metadata={"category": "ai_updated"}
        )
        self.provider.update([r1_mod])
        # Retrieve through search to check updated metadata
        res = self.provider.search(
            SearchRequest(
                embedding=[1.0, 0.0, 0.0],
                collection="col1",
                top_k=1
            )
        )
        self.assertEqual(res[0].vector_id, "v1")
        self.assertEqual(res[0].metadata["category"], "ai_updated")

        # Deleting records
        self.provider.delete("col1", ["v1"])
        res_after = self.provider.search(
            SearchRequest(
                embedding=[1.0, 0.0, 0.0],
                collection="col1",
                top_k=2
            )
        )
        # Only v2 should remain
        self.assertEqual(len(res_after), 1)
        self.assertEqual(res_after[0].vector_id, "v2")

    def test_similarity_search_and_routing(self) -> None:
        """Verifies similarity search calculations ordering, filters, and registry routing."""
        self.registry.register_provider("mem_p", self.provider)

        info = CollectionInfo(
            collection_id="col1",
            name="Collection One",
            dimensions=3,
            similarity_metric="cosine"
        )
        self.provider.create_collection(info)

        # Index points: v1 is parallel to query, v2 is orthogonal, v3 matches filter but is orthogonal
        v1 = VectorRecord(
            vector_id="v1",
            collection="col1",
            embedding=[1.0, 0.0, 0.0],
            metadata={"tag": "ai", "payload": {"text": "hello AI"}}
        )
        v2 = VectorRecord(
            vector_id="v2",
            collection="col1",
            embedding=[0.0, 1.0, 0.0],
            metadata={"tag": "math", "payload": {"text": "hello Math"}}
        )
        v3 = VectorRecord(
            vector_id="v3",
            collection="col1",
            embedding=[0.0, 0.0, 1.0],
            metadata={"tag": "ai", "payload": {"text": "hello other AI"}}
        )

        self.provider.insert([v1, v2, v3])

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Query parallel to v1, filtering for tag="ai"
        request = SearchRequest(
            embedding=[1.0, 0.0, 0.0],
            collection="col1",
            top_k=2,
            filters={"tag": "ai"}
        )

        response = self.registry.search("mem_p", request)

        # Output results checks
        # Results should be sorted by score descending: v1 (score 1.0) then v3 (score 0.0)
        self.assertEqual(len(response.results), 2)
        self.assertEqual(response.results[0].vector_id, "v1")
        self.assertAlmostEqual(response.results[0].score, 1.0)
        self.assertEqual(response.results[0].payload["text"], "hello AI")

        self.assertEqual(response.results[1].vector_id, "v3")
        self.assertAlmostEqual(response.results[1].score, 0.0)

        # Check events
        self.event_bus.dispatch_all()
        event_names = [e.payload["event_name"] for e in receiver.events]
        self.assertIn("vector.search.started", event_names)
        self.assertIn("vector.search.completed", event_names)

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent registrations and index search requests safety."""
        # Create collection
        info = CollectionInfo(
            collection_id="concur_col",
            name="Concur",
            dimensions=3,
            similarity_metric="dot_product"
        )
        self.provider.create_collection(info)

        num_threads = 10
        ops_per_thread = 15

        def worker(thread_idx: int) -> None:
            for i in range(ops_per_thread):
                rec = VectorRecord(
                    vector_id=f"t_{thread_idx}_v_{i}",
                    collection="concur_col",
                    embedding=[0.1, 0.2, 0.3],
                    metadata={"thread": thread_idx}
                )
                self.provider.insert([rec])

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Search all records
        res = self.provider.search(
            SearchRequest(
                embedding=[1.0, 1.0, 1.0],
                collection="concur_col",
                top_k=200
            )
        )
        self.assertEqual(len(res), num_threads * ops_per_thread)


if __name__ == "__main__":
    unittest.main()
