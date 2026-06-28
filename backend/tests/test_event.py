from datetime import datetime
import threading
from typing import List
import unittest
import uuid

from backend.runtime.event import (
    Event,
    EventBus,
    EventPriority,
    EventStatus,
    EventType,
    DuplicateSubscriptionError,
    SubscriptionNotFoundError,
    EventValidationError,
)


class MockHandler:
    """Mock handler class implementing the EventHandler protocol."""

    def __init__(self) -> None:
        self.received_events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.received_events.append(event)


class FailureHandler:
    """Mock handler designed to simulate processing failure."""

    def handle(self, event: Event) -> None:
        raise ValueError("Simulated handler error")


class TestEventSystem(unittest.TestCase):
    """Suite of tests covering the entire EventSystem lifecycle and safety features."""

    def setUp(self) -> None:
        self.bus = EventBus()
        self.bus.clear()

    def test_singleton(self) -> None:
        """Verifies that EventBus behaves as a singleton."""
        bus2 = EventBus()
        self.assertIs(self.bus, bus2)

    def test_serialization(self) -> None:
        """Verifies serialization/deserialization methods to_dict, from_dict, and copy."""
        event = Event(
            event_type=EventType.TASK_CREATED,
            priority=EventPriority.CRITICAL,
            source="source_agent",
            target="target_agent",
            payload={"task_id": "T100"},
            metadata={"debug": True}
        )

        cloned = event.copy()
        self.assertEqual(cloned.event_type, event.event_type)
        self.assertEqual(cloned.priority, event.priority)
        self.assertEqual(cloned.source, event.source)
        self.assertEqual(cloned.payload, event.payload)

        data = event.to_dict()
        self.assertEqual(data["event_type"], "TASK_CREATED")
        self.assertEqual(data["priority"], "CRITICAL")
        self.assertEqual(data["source"], "source_agent")

        deserialized = Event.from_dict(data)
        self.assertEqual(deserialized.event_id, event.event_id)
        self.assertEqual(deserialized.correlation_id, event.correlation_id)
        self.assertEqual(deserialized.event_type, event.event_type)
        self.assertEqual(deserialized.priority, event.priority)
        self.assertEqual(deserialized.payload, event.payload)

    def test_from_dict_validation_error(self) -> None:
        """Verifies that from_dict raises EventValidationError on malformed data."""
        with self.assertRaises(EventValidationError):
            Event.from_dict({"event_type": "INVALID_TYPE"})

    def test_subscribe_and_publish(self) -> None:
        """Verifies event subscription, publishing, and dispatching."""
        handler = MockHandler()
        self.bus.subscribe(EventType.TASK_CREATED, handler)

        event = Event(
            event_type=EventType.TASK_CREATED,
            priority=EventPriority.HIGH,
            payload={"task_id": "T100"}
        )
        self.bus.publish(event)

        self.assertEqual(self.bus.event_count(), 1)
        self.assertEqual(len(self.bus.pending_events()), 1)
        self.assertEqual(event.status, EventStatus.QUEUED)

        dispatched = self.bus.dispatch()
        self.assertIs(dispatched, event)

        self.assertEqual(self.bus.event_count(), 0)
        self.assertEqual(len(handler.received_events), 1)
        self.assertIs(handler.received_events[0], event)
        self.assertEqual(event.status, EventStatus.COMPLETED)
        self.assertIsNotNone(event.processed_at)

    def test_duplicate_subscription_raises(self) -> None:
        """Verifies that duplicate subscriptions raise the proper exception."""
        handler = MockHandler()
        self.bus.subscribe(EventType.TASK_CREATED, handler)

        with self.assertRaises(DuplicateSubscriptionError):
            self.bus.subscribe(EventType.TASK_CREATED, handler)

    def test_unsubscribe(self) -> None:
        """Verifies unsubscription mechanics and corresponding errors."""
        handler = MockHandler()
        self.bus.subscribe(EventType.TASK_CREATED, handler)
        self.assertEqual(self.bus.subscriber_count(EventType.TASK_CREATED), 1)

        self.bus.unsubscribe(EventType.TASK_CREATED, handler)
        self.assertEqual(self.bus.subscriber_count(EventType.TASK_CREATED), 0)

        with self.assertRaises(SubscriptionNotFoundError):
            self.bus.unsubscribe(EventType.TASK_CREATED, handler)

    def test_wildcard_subscription(self) -> None:
        """Verifies that wildcard subscription receives all event types."""
        handler = MockHandler()
        self.bus.subscribe("*", handler)

        e1 = Event(event_type=EventType.TASK_CREATED)
        e2 = Event(event_type=EventType.AGENT_REGISTERED)

        self.bus.publish(e1)
        self.bus.publish(e2)

        self.bus.dispatch_all()

        self.assertEqual(len(handler.received_events), 2)
        self.assertIn(e1, handler.received_events)
        self.assertIn(e2, handler.received_events)

    def test_invalid_wildcard_subscription_raises(self) -> None:
        """Verifies string subscription validation."""
        handler = MockHandler()
        with self.assertRaises(EventValidationError):
            self.bus.subscribe("INVALID_WILDCARD", handler)

    def test_event_filtering(self) -> None:
        """Verifies subscription filters selectively invoke handlers."""
        handler = MockHandler()
        filter_func = lambda e: e.payload.get("status") == "critical"

        self.bus.subscribe(EventType.SYSTEM_EVENT, handler, filter_func=filter_func)

        e_match = Event(event_type=EventType.SYSTEM_EVENT, payload={"status": "critical"})
        e_skip = Event(event_type=EventType.SYSTEM_EVENT, payload={"status": "info"})

        self.bus.publish(e_match)
        self.bus.publish(e_skip)
        self.bus.dispatch_all()

        self.assertEqual(len(handler.received_events), 1)
        self.assertIs(handler.received_events[0], e_match)

    def test_event_filter_exception_isolation(self) -> None:
        """Verifies filter exception doesn't halt event system."""
        handler = MockHandler()
        def bad_filter(event: Event) -> bool:
            raise RuntimeError("Filter error")

        self.bus.subscribe(EventType.SYSTEM_EVENT, handler, filter_func=bad_filter)

        event = Event(event_type=EventType.SYSTEM_EVENT)
        self.bus.publish(event)
        self.bus.dispatch_all()

        self.assertEqual(event.status, EventStatus.FAILED)
        self.assertEqual(len(event.metadata["errors"]), 1)
        self.assertIn("Filter error", event.metadata["errors"][0]["error"])

    def test_priority_ordering(self) -> None:
        """Verifies events are dispatched in priority-first sequence."""
        handler = MockHandler()
        self.bus.subscribe(EventType.TASK_CREATED, handler)

        e_low = Event(event_type=EventType.TASK_CREATED, priority=EventPriority.LOW)
        e_high = Event(event_type=EventType.TASK_CREATED, priority=EventPriority.HIGH)
        e_critical = Event(event_type=EventType.TASK_CREATED, priority=EventPriority.CRITICAL)
        e_normal = Event(event_type=EventType.TASK_CREATED, priority=EventPriority.NORMAL)

        # Publish out of order
        self.bus.publish(e_low)
        self.bus.publish(e_high)
        self.bus.publish(e_critical)
        self.bus.publish(e_normal)

        # Dispatch all
        self.bus.dispatch_all()

        # Check dispatch sequence
        self.assertEqual(handler.received_events[0], e_critical)
        self.assertEqual(handler.received_events[1], e_high)
        self.assertEqual(handler.received_events[2], e_normal)
        self.assertEqual(handler.received_events[3], e_low)

    def test_handler_failure_isolation(self) -> None:
        """Verifies failure in one handler doesn't impact other subscribers."""
        h1 = MockHandler()
        h_fail = FailureHandler()
        h2 = MockHandler()

        self.bus.subscribe(EventType.ERROR_OCCURRED, h1)
        self.bus.subscribe(EventType.ERROR_OCCURRED, h_fail)
        self.bus.subscribe(EventType.ERROR_OCCURRED, h2)

        event = Event(event_type=EventType.ERROR_OCCURRED)
        self.bus.publish(event)
        self.bus.dispatch_all()

        self.assertEqual(len(h1.received_events), 1)
        self.assertEqual(len(h2.received_events), 1)

        self.assertEqual(event.status, EventStatus.FAILED)
        self.assertIn("errors", event.metadata)
        self.assertEqual(len(event.metadata["errors"]), 1)
        self.assertIn("Simulated handler error", event.metadata["errors"][0]["error"])

    def test_history_and_processed_events(self) -> None:
        """Verifies processing history indexing."""
        e1 = Event(event_type=EventType.TASK_STARTED)
        e2 = Event(event_type=EventType.TASK_COMPLETED)

        self.bus.publish(e1)
        self.bus.publish(e2)

        self.assertEqual(self.bus.event_count(), 2)
        self.bus.dispatch_all()

        history = self.bus.history()
        self.assertEqual(len(history), 2)
        self.assertIs(history[0], e1)
        self.assertIs(history[1], e2)

    def test_statistics(self) -> None:
        """Verifies statistics metrics accuracy."""
        h_fail = FailureHandler()
        self.bus.subscribe(EventType.TASK_FAILED, h_fail)

        e1 = Event(event_type=EventType.TASK_FAILED)
        e2 = Event(event_type=EventType.TASK_STARTED)

        self.bus.publish(e1)
        self.bus.publish(e2)
        self.bus.dispatch_all()

        stats = self.bus.statistics()
        self.assertEqual(stats["published_count"], 2)
        self.assertEqual(stats["dispatched_count"], 2)
        self.assertEqual(stats["failed_count"], 1)
        self.assertEqual(stats["by_type"][EventType.TASK_FAILED.value]["published"], 1)
        self.assertEqual(stats["by_type"][EventType.TASK_FAILED.value]["failed"], 1)
        self.assertEqual(stats["by_type"][EventType.TASK_STARTED.value]["published"], 1)
        self.assertEqual(stats["by_type"][EventType.TASK_STARTED.value]["failed"], 0)

    def test_has_subscribers(self) -> None:
        """Verifies subscriber check method logic."""
        self.assertFalse(self.bus.has_subscribers())
        self.assertFalse(self.bus.has_subscribers(EventType.TASK_CREATED))

        handler = MockHandler()
        self.bus.subscribe(EventType.TASK_CREATED, handler)
        self.assertTrue(self.bus.has_subscribers())
        self.assertTrue(self.bus.has_subscribers(EventType.TASK_CREATED))
        self.assertFalse(self.bus.has_subscribers(EventType.AGENT_REGISTERED))

        # Check that wildcard subscription matches any type
        wild_bus = EventBus()
        wild_bus.clear()
        wild_bus.subscribe("*", handler)
        self.assertTrue(wild_bus.has_subscribers())
        self.assertTrue(wild_bus.has_subscribers(EventType.TASK_CREATED))

    def test_dispatch_empty_queue_returns_none(self) -> None:
        """Verifies dispatching on empty queue returns None."""
        self.assertIsNone(self.bus.dispatch())

    def test_thread_safety(self) -> None:
        """Verifies that publishing and dispatching is thread-safe under load."""
        num_threads = 15
        events_per_thread = 40

        def publisher() -> None:
            for _ in range(events_per_thread):
                self.bus.publish(Event(event_type=EventType.MEMORY_UPDATED))

        threads = [threading.Thread(target=publisher) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.bus.event_count(), num_threads * events_per_thread)

        handler = MockHandler()
        self.bus.subscribe(EventType.MEMORY_UPDATED, handler)

        self.bus.dispatch_all()
        self.assertEqual(len(handler.received_events), num_threads * events_per_thread)
        self.assertEqual(self.bus.statistics()["published_count"], num_threads * events_per_thread)


if __name__ == "__main__":
    unittest.main()
