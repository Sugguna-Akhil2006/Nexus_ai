"""Tests for trace diff and comparison capabilities."""

import unittest

from backend.reasoning_studio.models import DiffStatus
from backend.reasoning_studio.reasoning_diff import ReasoningDiff
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.reasoning_studio.trace_comparator import TraceComparator
from backend.runtime.event import EventBus

from backend.reasoning_studio.tests.test_trace import _reset_bus, make_execution_trace


class TestReasoningDiff(unittest.TestCase):
    """Validates diff logic between identical, similar, and divergent traces."""

    def setUp(self) -> None:
        _reset_bus()
        self.store = ReasoningTrace()
        self.comparator = TraceComparator(self.store)

    def test_identical_traces_have_similarity_one(self) -> None:
        """Two traces with identical steps must have similarity_score == 1.0."""
        t = make_execution_trace(execution_id="exec-a", num_steps=3)
        s1 = self.store.ingest_execution_trace(t)
        # Re-ingest under a different execution ID to get a second trace ID
        t2 = make_execution_trace(execution_id="exec-b", num_steps=3)
        s2 = self.store.ingest_execution_trace(t2)

        diff = ReasoningDiff.diff(s1, s2)
        self.assertAlmostEqual(diff.similarity_score, 1.0, places=2)
        unchanged_steps = [d for d in diff.step_diffs if d.status == DiffStatus.UNCHANGED]
        self.assertEqual(len(unchanged_steps), 3)

    def test_different_step_counts_produce_added_removed(self) -> None:
        """Mismatched trace lengths must produce ADDED/REMOVED diff entries."""
        short_trace = self.store.ingest_execution_trace(
            make_execution_trace(execution_id="exec-short", num_steps=2)
        )
        long_trace = self.store.ingest_execution_trace(
            make_execution_trace(execution_id="exec-long", num_steps=5)
        )

        diff = ReasoningDiff.diff(short_trace, long_trace)
        # 3 extra steps in right → ADDED entries
        added = [d for d in diff.step_diffs if d.status == DiffStatus.ADDED]
        self.assertEqual(len(added), 3)
        self.assertLess(diff.similarity_score, 1.0)

    def test_comparator_publishes_event(self) -> None:
        """TraceComparator.compare() must publish reasoning.compared event."""
        from backend.runtime.event import EventType

        received: list = []

        class Recv:
            def handle(self, e):
                received.append(e)

        recv = Recv()
        _reset_bus()
        bus = EventBus()
        bus.subscribe(EventType.REASONING_COMPARED, recv)

        store = ReasoningTrace(event_bus=bus)
        comp = TraceComparator(store, event_bus=bus)

        s1 = store.ingest_execution_trace(make_execution_trace("exec-c1", num_steps=2))
        s2 = store.ingest_execution_trace(make_execution_trace("exec-c2", num_steps=2))

        comp.compare(s1.studio_trace_id, s2.studio_trace_id)
        bus.dispatch_all()
        self.assertEqual(len(received), 1)

    def test_comparator_raises_for_missing_trace(self) -> None:
        """Comparing a missing trace must raise ValueError."""
        s = self.store.ingest_execution_trace(make_execution_trace("exec-d"))
        with self.assertRaises(ValueError):
            self.comparator.compare(s.studio_trace_id, "non-existent")

    def test_total_changed_count(self) -> None:
        """total_changed must equal the number of non-UNCHANGED diffs across all fields."""
        short = self.store.ingest_execution_trace(make_execution_trace("exec-e", num_steps=1))
        longer = self.store.ingest_execution_trace(make_execution_trace("exec-f", num_steps=3))
        diff = ReasoningDiff.diff(short, longer)
        # 2 added steps × 3 fields (step, confidence, provider) = 6 changed entries
        self.assertEqual(diff.total_changed, 6)
