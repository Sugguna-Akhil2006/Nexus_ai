from datetime import datetime, timedelta
import threading
from typing import Any, Dict, List
import unittest
import uuid

from core.context import (
    ContextDeduplicator,
    ContextError,
    ContextProvider,
    ContextRankingStrategy,
    ContextRegistry,
    ContextRequest,
    ContextSection,
    ContextSource,
    ContextValidationError,
    DefaultContextRankingStrategy,
    ProviderNotFoundError,
    TokenBudgetManager,
)
from core.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class DummyContextProvider(ContextProvider):
    """Custom context provider implementation for testing."""

    def __init__(
        self,
        supported_sources: List[ContextSource],
        sections: List[ContextSection]
    ) -> None:
        self.supported_sources = supported_sources
        self.sections = sections

    def collect(self, request: ContextRequest) -> List[ContextSection]:
        # Return only sections that match requested sources
        requested = set(request.required_sources + request.optional_sources)
        return [
            s for s in self.sections
            if s.source in requested or not requested
        ]

    def supports(self, source: ContextSource) -> bool:
        return source in self.supported_sources

    def health_check(self) -> bool:
        return True


class CustomRankingStrategy(ContextRankingStrategy):
    """Custom strategy that reverse ranks by relevance."""

    def rank(self, sections: List[ContextSection]) -> List[ContextSection]:
        sorted_sections = list(sections)
        sorted_sections.sort(key=lambda s: s.relevance_score)  # Ascending
        return sorted_sections


class TestContextSystem(unittest.TestCase):
    """Suite of tests covering the Context Engine and Registry system."""

    def setUp(self) -> None:
        self.registry = ContextRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
            self.registry.set_ranking_strategy(DefaultContextRankingStrategy())
        self.event_bus = EventBus()
        self.event_bus.clear()

    def test_singleton(self) -> None:
        """Verifies that ContextRegistry behaves as a singleton."""
        registry2 = ContextRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration_validation(self) -> None:
        """Verifies registrations enforce uniqueness constraints and validate fields."""
        provider = DummyContextProvider(
            supported_sources=[ContextSource.USER],
            sections=[]
        )

        # Successful registration
        self.registry.register_provider("user_prov", provider)
        self.assertIn("user_prov", self.registry.list_providers())

        # Duplicate ID raises ContextValidationError
        with self.assertRaises(ContextValidationError):
            self.registry.register_provider("user_prov", provider)

        # Unregistering provider
        self.registry.unregister_provider("user_prov")
        self.assertNotIn("user_prov", self.registry.list_providers())

        with self.assertRaises(ProviderNotFoundError):
            self.registry.unregister_provider("user_prov")

    def test_deduplication(self) -> None:
        """Verifies deduplicator removes duplicate IDs and duplicate content."""
        s1 = ContextSection("sec1", ContextSource.USER, "Title", "Dup Content", 0.9, 10)
        s2 = ContextSection("sec1", ContextSource.USER, "Title", "Dup Content", 0.9, 10)
        s3 = ContextSection("sec2", ContextSource.SYSTEM, "Title 2", "Dup Content", 0.8, 10)
        s4 = ContextSection("sec3", ContextSource.SYSTEM, "Title 3", "Unique Content", 0.8, 10)

        raw = [s1, s2, s3, s4]
        unique = ContextDeduplicator.deduplicate(raw)

        # s2 is duplicate ID, s3 is duplicate content -> only s1 and s4 should remain
        self.assertEqual(len(unique), 2)
        self.assertEqual(unique[0].section_id, "sec1")
        self.assertEqual(unique[1].section_id, "sec3")

    def test_token_budget_trimming(self) -> None:
        """Verifies TokenBudgetManager trims optional items while preserving required ones."""
        # Required System section (30 tokens)
        s_req = ContextSection("sec_req", ContextSource.SYSTEM, "Req", "Req Content", 0.5, 30)
        # Optional Vector sections
        s_opt1 = ContextSection("sec_opt1", ContextSource.VECTOR, "Opt 1", "Opt 1 Content", 0.9, 40)
        s_opt2 = ContextSection("sec_opt2", ContextSource.VECTOR, "Opt 2", "Opt 2 Content", 0.8, 40)

        # Case 1: Max tokens = 80
        # Should pick s_req (30) + s_opt1 (40) = 70. s_opt2 (40) is trimmed (would exceed 80).
        budget_manager = TokenBudgetManager(max_tokens=80)
        sorted_sections = [s_opt1, s_opt2, s_req]  # already sorted by relevance (opt1, opt2, req)

        trimmed = budget_manager.enforce(
            sorted_sections,
            required_sources=[ContextSource.SYSTEM]
        )

        self.assertEqual(len(trimmed), 2)
        self.assertIn(s_req, trimmed)
        self.assertIn(s_opt1, trimmed)
        self.assertNotIn(s_opt2, trimmed)
        self.assertEqual(len(budget_manager.discarded_sections), 1)
        self.assertIn(s_opt2, budget_manager.discarded_sections)

    def test_ranking_strategy(self) -> None:
        """Verifies DefaultContextRankingStrategy ranks by relevance, priority, recency."""
        ts_now = datetime.utcnow()
        ts_old = ts_now - timedelta(days=1)

        # Section 1: relevance 0.9, source USER, old
        s1 = ContextSection(
            "s1", ContextSource.USER, "S1", "C1", 0.9, 10,
            metadata={"timestamp": ts_old.isoformat()}
        )
        # Section 2: relevance 0.9, source USER, now (newer than s1)
        s2 = ContextSection(
            "s2", ContextSource.USER, "S2", "C2", 0.9, 10,
            metadata={"timestamp": ts_now.isoformat()}
        )
        # Section 3: relevance 0.8, source SYSTEM (high source priority)
        s3 = ContextSection(
            "s3", ContextSource.SYSTEM, "S3", "C3", 0.8, 10,
            metadata={"timestamp": ts_now.isoformat()}
        )

        # Rank s1, s2, s3:
        # Relevance: s1 and s2 rank higher than s3 (0.9 vs 0.8).
        # Between s1 and s2: same relevance, same source. s2 is newer than s1 -> s2 ranks above s1.
        # Order should be: s2, s1, s3
        strategy = DefaultContextRankingStrategy()
        ranked = strategy.rank([s1, s3, s2])

        self.assertEqual(ranked[0].section_id, "s2")
        self.assertEqual(ranked[1].section_id, "s1")
        self.assertEqual(ranked[2].section_id, "s3")

    def test_pluggable_ranking_strategy(self) -> None:
        """Verifies registering a custom ranking strategy overrides default behaviors."""
        s1 = ContextSection("s1", ContextSource.USER, "S1", "C1", 0.9, 10)
        s2 = ContextSection("s2", ContextSource.USER, "S2", "C2", 0.7, 10)

        # Default strategy ranks s1 above s2
        self.registry.register_provider("prov", DummyContextProvider([], [s1, s2]))
        res_default = self.registry.collect(ContextRequest(max_tokens=100))
        self.assertEqual(res_default.context.sections[0].section_id, "s1")

        # Set custom ranking strategy (ascending relevance)
        self.registry.set_ranking_strategy(CustomRankingStrategy())
        res_custom = self.registry.collect(ContextRequest(max_tokens=100))
        self.assertEqual(res_custom.context.sections[0].section_id, "s2")

    def test_collect_lifecycle_and_events(self) -> None:
        """Verifies context aggregation workflow and event triggers."""
        ts_now = datetime.utcnow()
        s1 = ContextSection(
            "sec1", ContextSource.USER, "U", "User details", 0.95, 20,
            metadata={"timestamp": ts_now.isoformat()}
        )
        s2 = ContextSection(
            "sec2", ContextSource.VECTOR, "V", "Vector context", 0.85, 25,
            metadata={"timestamp": ts_now.isoformat()}
        )

        provider = DummyContextProvider(
            supported_sources=[ContextSource.USER, ContextSource.VECTOR],
            sections=[s1, s2]
        )
        self.registry.register_provider("p1", provider)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        request = ContextRequest(
            max_tokens=100,
            required_sources=[ContextSource.USER],
            optional_sources=[ContextSource.VECTOR]
        )

        response = self.registry.collect(request)

        # Verify Response Payload
        self.assertEqual(response.token_usage["total_tokens"], 45)
        self.assertEqual(len(response.context.sections), 2)
        self.assertEqual(response.context.sections[0].section_id, "sec1")

        # Check events
        self.event_bus.dispatch_all()
        event_names = [e.payload["event_name"] for e in receiver.events]
        self.assertIn("context.collection.started", event_names)
        self.assertIn("context.collection.completed", event_names)

    def test_thread_safety_concurrency(self) -> None:
        """Verifies concurrent context collection request executions."""
        # Register a provider with some static context
        s1 = ContextSection("s1", ContextSource.USER, "S1", "C1", 0.9, 10)
        provider = DummyContextProvider([ContextSource.USER], [s1])
        self.registry.register_provider("prov", provider)

        num_threads = 10
        requests_per_thread = 15

        results = []
        results_lock = threading.Lock()

        def worker() -> None:
            for _ in range(requests_per_thread):
                req = ContextRequest(max_tokens=100, required_sources=[ContextSource.USER])
                res = self.registry.collect(req)
                with results_lock:
                    results.append(res)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), num_threads * requests_per_thread)
        for res in results:
            self.assertEqual(len(res.context.sections), 1)
            self.assertEqual(res.context.sections[0].section_id, "s1")


if __name__ == "__main__":
    unittest.main()
