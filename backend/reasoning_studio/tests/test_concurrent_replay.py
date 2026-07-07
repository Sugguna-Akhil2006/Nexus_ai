"""Tests for concurrent replay sessions and thread-safe Studio operations."""

import concurrent.futures
import threading
import unittest

from backend.reasoning_studio.models import ReplayState
from backend.reasoning_studio.reasoning_replay import ReasoningReplay
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.reasoning_studio.studio_api import StudioAPI
from backend.runtime.event import EventBus

from backend.reasoning_studio.tests.test_trace import _reset_bus, make_execution_trace


class TestConcurrentReplay(unittest.TestCase):
    """Validates thread safety across simultaneous replay sessions."""

    def setUp(self) -> None:
        _reset_bus()

    def test_concurrent_trace_ingestion(self) -> None:
        """Multiple threads ingesting traces concurrently must not corrupt the store."""
        store = ReasoningTrace()

        def ingest(idx: int) -> str:
            t = make_execution_trace(execution_id=f"exec-conc-{idx}", num_steps=3)
            studio = store.ingest_execution_trace(t)
            return studio.studio_trace_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            ids = list(pool.map(ingest, range(20)))

        self.assertEqual(len(set(ids)), 20)          # all unique
        self.assertEqual(len(store.list_traces()), 20)

    def test_concurrent_replay_sessions(self) -> None:
        """Parallel replay sessions on different traces must remain isolated."""
        store = ReasoningTrace()
        replay = ReasoningReplay(store)

        # Pre-ingest 10 traces
        trace_ids = []
        for i in range(10):
            t = make_execution_trace(execution_id=f"exec-rep-{i}", num_steps=5)
            studio = store.ingest_execution_trace(t)
            trace_ids.append(studio.studio_trace_id)

        results: dict[str, int] = {}
        lock = threading.Lock()

        def run_replay(trace_id: str) -> None:
            session = replay.create_session(trace_id)
            replay.start(session.session_id)
            count = 0
            while True:
                step = replay.next_step(session.session_id)
                if step is None:
                    break
                count += 1
            with lock:
                results[trace_id] = count

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            list(pool.map(run_replay, trace_ids))

        for tid in trace_ids:
            self.assertEqual(results[tid], 5)

    def test_concurrent_studio_api_reads(self) -> None:
        """Concurrent console display data reads must not raise exceptions."""
        api = StudioAPI()
        t = make_execution_trace(execution_id="exec-api-conc", num_steps=8)
        studio = api.ingest(t)
        trace_id = studio.studio_trace_id

        errors: list[Exception] = []

        def read(_: int) -> None:
            try:
                api.get_confidence_analysis(trace_id)
                api.get_decision_graph(trace_id)
                api.get_timeline(trace_id)
                api.get_explanation(trace_id)
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(read, range(24)))

        self.assertEqual(errors, [])

    def test_concurrent_comparisons(self) -> None:
        """Parallel diff operations must produce correct isolated results."""
        store = ReasoningTrace()
        from backend.reasoning_studio.trace_comparator import TraceComparator
        comp = TraceComparator(store)

        left = store.ingest_execution_trace(make_execution_trace("exec-cmp-L", num_steps=3))
        right = store.ingest_execution_trace(make_execution_trace("exec-cmp-R", num_steps=3))

        diffs = []
        lock = threading.Lock()

        def do_compare(_: int) -> None:
            d = comp.compare(left.studio_trace_id, right.studio_trace_id)
            with lock:
                diffs.append(d.similarity_score)

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(do_compare, range(12)))

        # All concurrent diffs must agree on similarity
        self.assertTrue(all(abs(s - diffs[0]) < 1e-6 for s in diffs))
