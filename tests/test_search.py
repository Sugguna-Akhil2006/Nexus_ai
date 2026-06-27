import concurrent.futures
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from core.search import (
    SearchError,
    SearchValidationError,
    SearchProviderError,
    SearchMode,
    SearchFilter,
    SearchRequest,
    SearchResult,
    SearchResponse,
    RankingStrategy,
    CosineScoreRankingStrategy,
    HybridWeightedRankingStrategy,
    SearchProvider,
    MockSearchProvider,
    SearchRegistry,
    SearchAgent,
    validate_search_request,
)
from core.base import AgentState, AgentStatus
from core.event import Event, EventBus, EventType
from core.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestSearchSystem(unittest.TestCase):
    """Suite of tests covering pluggable ranking and federated search retrieval."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = SearchRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
        self.provider = MockSearchProvider()
        self.registry.register_provider("mock", self.provider)

        self.agent = SearchAgent()
        self.agent.initialize()

    def test_ranking_strategies(self) -> None:
        """Verifies pluggable ranking strategies output correctly sorted and weighted arrays."""
        results = [
            SearchResult("r1", "d1", "c1", 0.80, "snippet 1", "source", {"keyword_score": 0.60}),
            SearchResult("r2", "d2", "c2", 0.90, "snippet 2", "source", {"keyword_score": 0.95})
        ]

        # 1. Cosine Ranking
        cosine = CosineScoreRankingStrategy()
        ranked_cos = cosine.rank(results)
        self.assertEqual(ranked_cos[0].result_id, "r2")
        self.assertEqual(ranked_cos[1].result_id, "r1")

        # 2. Hybrid Weighted Ranking (weight: 0.7 semantic, 0.3 keyword)
        # r1 combined: 0.80 * 0.7 + 0.60 * 0.3 = 0.56 + 0.18 = 0.74
        # r2 combined: 0.90 * 0.7 + 0.95 * 0.3 = 0.63 + 0.285 = 0.915
        hybrid = HybridWeightedRankingStrategy(semantic_weight=0.7, keyword_weight=0.3)
        ranked_hyb = hybrid.rank(results)
        self.assertEqual(ranked_hyb[0].result_id, "r2")
        self.assertEqual(ranked_hyb[0].score, 0.915)
        self.assertEqual(ranked_hyb[1].result_id, "r1")
        self.assertEqual(ranked_hyb[1].score, 0.74)

    def test_validation_utilities(self) -> None:
        """Verifies validation constraints reject bad parameter request options."""
        # Valid Request
        req = SearchRequest(
            request_id="req_1",
            workspace_id="ws_1",
            query="search term",
            search_mode=SearchMode.SEMANTIC,
            collections=["collection_1"],
            filters=[SearchFilter("owner", "eq", "user_123")],
            top_k=5
        )
        validate_search_request(req)

        # Empty Query
        with self.assertRaises(SearchValidationError):
            validate_search_request(SearchRequest("r", "ws", "", SearchMode.SEMANTIC, ["col"]))

        # Negative top_k
        with self.assertRaises(SearchValidationError):
            validate_search_request(SearchRequest("r", "ws", "term", SearchMode.SEMANTIC, ["col"], top_k=-1))

        # Empty Collections
        with self.assertRaises(SearchValidationError):
            validate_search_request(SearchRequest("r", "ws", "term", SearchMode.SEMANTIC, []))

        # Invalid Filter (missing field/operator)
        invalid_filter = SearchFilter("", "eq", "value")
        with self.assertRaises(SearchValidationError):
            validate_search_request(SearchRequest("r", "ws", "term", SearchMode.SEMANTIC, ["col"], [invalid_filter]))

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of SearchRegistry."""
        registry2 = SearchRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration(self) -> None:
        """Verifies provider register and unregister constraints on SearchRegistry."""
        with self.assertRaises(SearchValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(SearchValidationError):
            self.registry.register_provider("mock2", None)  # type: ignore
        with self.assertRaises(SearchValidationError):
            self.registry.register_provider("mock", self.provider)  # duplicate check

        self.registry.unregister_provider("mock")
        self.assertNotIn("mock", self.registry.list_providers())

    def test_agent_search_semantic(self) -> None:
        """Verifies execution of semantic search task and EventBus notification signals."""
        task = Task(
            description="Semantic search query",
            metadata={
                "action": "search",
                "workspace_id": "workspace_1",
                "query": "artificial intelligence",
                "collections": ["wiki"],
                "search_mode": "SEMANTIC",
                "ranking_strategy": "cosine"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: SearchResponse = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(res.provider, "mock")
        self.assertEqual(len(res.results), 2)
        self.assertEqual(res.results[0].document_id, "doc_semantic_1")
        self.assertIn("artificial intelligence", res.results[0].snippet)

        # Confirm EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("search.started", events)
        self.assertIn("search.results.ranked", events)
        self.assertIn("search.completed", events)

    def test_agent_search_keyword(self) -> None:
        """Verifies keyword search mode execution."""
        task = Task(
            description="Keyword search query",
            metadata={
                "action": "search",
                "workspace_id": "workspace_1",
                "query": "intelligence",
                "collections": ["wiki"],
                "search_mode": "KEYWORD"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: SearchResponse = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(len(res.results), 1)
        self.assertEqual(res.results[0].document_id, "doc_keyword_1")
        self.assertIn("intelligence", res.results[0].snippet)

    def test_agent_search_hybrid(self) -> None:
        """Verifies hybrid search mode execution with weighting ranker."""
        task = Task(
            description="Hybrid search query",
            metadata={
                "action": "search",
                "workspace_id": "workspace_1",
                "query": "agent framework",
                "collections": ["wiki"],
                "search_mode": "HYBRID",
                "ranking_strategy": "hybrid_weighted"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: SearchResponse = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(len(res.results), 1)
        self.assertEqual(res.results[0].document_id, "doc_hybrid_1")
        self.assertIn("agent framework", res.results[0].snippet)
        # combined: 0.90 * 0.7 + 0.80 * 0.3 = 0.63 + 0.24 = 0.87
        self.assertEqual(res.results[0].score, 0.87)

    def test_agent_suggest_task(self) -> None:
        """Verifies suggests retrieval task parsing query keywords."""
        task = Task(
            description="Suggest query completions",
            metadata={
                "action": "suggest",
                "query": "agen",
                "limit": 3
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        suggestions = self.agent.execute(task)
        self.agent.after_execute(suggestions)

        self.assertEqual(len(suggestions), 3)
        self.assertEqual(suggestions[0], "agen suggestion 1")

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            class DummySearchProvider(SearchProvider):
                def search(self, request): return []
                def search_keyword(self, request): return []
                def search_hybrid(self, request): return []
                def suggest(self, query, limit=5): return []
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummySearchProvider())
            self.assertIn(pid, self.registry._providers)
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
