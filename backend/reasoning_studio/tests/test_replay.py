"""Tests for step-by-step and full-run replay, pause, resume, and jump-to."""

import unittest

from backend.reasoning_studio.models import ReplayState
from backend.reasoning_studio.reasoning_replay import ReasoningReplay
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.runtime.event import EventBus

from backend.reasoning_studio.tests.test_trace import _reset_bus, make_execution_trace


class TestReasoning_Replay(unittest.TestCase):
    """Validates the replay engine lifecycle and step traversal."""

    def setUp(self) -> None:
        _reset_bus()
        self.store = ReasoningTrace()
        self.replay = ReasoningReplay(self.store)

        exec_trace = make_execution_trace(num_steps=5)
        self.studio = self.store.ingest_execution_trace(exec_trace)
        self.trace_id = self.studio.studio_trace_id

    def test_full_replay_returns_all_steps(self) -> None:
        """replay_all() must return every captured step in order."""
        steps = self.replay.replay_all(self.trace_id)
        self.assertEqual(len(steps), 5)
        for i, step in enumerate(steps):
            self.assertEqual(step.sequence_index, i)

    def test_step_by_step_traversal(self) -> None:
        """Starting a session and calling next_step() should advance the cursor."""
        session = self.replay.create_session(self.trace_id)
        self.replay.start(session.session_id)

        steps_returned = []
        while True:
            step = self.replay.next_step(session.session_id)
            if step is None:
                break
            steps_returned.append(step)

        self.assertEqual(len(steps_returned), 5)
        s = self.replay.get_session(session.session_id)
        self.assertEqual(s.state, ReplayState.COMPLETED)

    def test_pause_and_resume(self) -> None:
        """Pause must stop advancement; resume must continue from same position."""
        session = self.replay.create_session(self.trace_id)
        self.replay.start(session.session_id)

        first_step = self.replay.next_step(session.session_id)
        self.assertIsNotNone(first_step)

        self.replay.pause(session.session_id)
        s = self.replay.get_session(session.session_id)
        self.assertEqual(s.state, ReplayState.PAUSED)

        # next_step on a paused session returns None
        no_step = self.replay.next_step(session.session_id)
        self.assertIsNone(no_step)

        # Resume
        self.replay.start(session.session_id)
        second_step = self.replay.next_step(session.session_id)
        self.assertIsNotNone(second_step)
        self.assertEqual(second_step.sequence_index, 1)

    def test_jump_to_decision(self) -> None:
        """jump_to() must reposition the cursor without advancing."""
        session = self.replay.create_session(self.trace_id)
        self.replay.start(session.session_id)
        self.replay.jump_to(session.session_id, 3)

        s = self.replay.get_session(session.session_id)
        self.assertEqual(s.current_step_index, 3)
        self.assertEqual(s.state, ReplayState.PAUSED)

    def test_jump_to_out_of_range_raises(self) -> None:
        """jump_to() with an invalid index must raise ValueError."""
        session = self.replay.create_session(self.trace_id)
        with self.assertRaises(ValueError):
            self.replay.jump_to(session.session_id, 99)

    def test_unknown_trace_raises(self) -> None:
        """Creating a session for a missing trace must raise ValueError."""
        with self.assertRaises(ValueError):
            self.replay.create_session("no-such-trace")
