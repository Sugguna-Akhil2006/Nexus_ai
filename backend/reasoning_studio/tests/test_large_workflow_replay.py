"""Tests for large workflow replay — verifies scalability and correctness at scale."""

import unittest

from backend.observability.models import ExecutionTrace, PromptMetadata, ReasoningStep, SpanStatus
from backend.reasoning_studio.decision_graph import DecisionGraphBuilder
from backend.reasoning_studio.reasoning_replay import ReasoningReplay
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.reasoning_studio.timeline_replayer import TimelineReplayer
from backend.runtime.event import EventBus

from backend.reasoning_studio.tests.test_trace import _reset_bus


def make_large_trace(
    execution_id: str,
    num_steps: int = 200,
    add_tool_calls: bool = True,
) -> ExecutionTrace:
    """Builds a large ExecutionTrace for stress testing."""
    steps = []
    for i in range(num_steps):
        steps.append(ReasoningStep(
            description=f"Large step {i}: processing complex multi-hop reasoning",
            inputs={"step": i, "data": [j for j in range(10)]},
            outputs={"result": i * 3},
            confidence=max(0.5, 1.0 - i * 0.001),
        ))

    trace = ExecutionTrace(
        execution_id=execution_id,
        workflow_id="wf-large",
        workspace_id="ws-stress",
        reasoning_steps=steps,
        status=SpanStatus.COMPLETED,
        prompt_metadata=PromptMetadata(
            template_name="large-v2",
            model="claude-3-5-sonnet",
            provider="anthropic",
            token_count=8000,
        ),
    )
    trace.total_duration_ms = num_steps * 50.0
    return trace


class TestLargeWorkflowReplay(unittest.TestCase):
    """Validates that the Studio handles large traces without errors."""

    def setUp(self) -> None:
        _reset_bus()
        self.store = ReasoningTrace()
        self.replay = ReasoningReplay(self.store)

    def test_ingest_200_step_trace(self) -> None:
        """Should ingest a 200-step trace without data loss."""
        large = make_large_trace("exec-large-1", num_steps=200)
        studio = self.store.ingest_execution_trace(large)
        self.assertEqual(studio.total_steps, 200)

    def test_full_replay_200_steps(self) -> None:
        """replay_all() must return all 200 steps in order."""
        large = make_large_trace("exec-large-2", num_steps=200)
        studio = self.store.ingest_execution_trace(large)
        steps = self.replay.replay_all(studio.studio_trace_id)
        self.assertEqual(len(steps), 200)
        for i, s in enumerate(steps):
            self.assertEqual(s.sequence_index, i)

    def test_decision_graph_200_steps(self) -> None:
        """Decision graph must have at least 200 decision nodes for a 200-step trace."""
        large = make_large_trace("exec-large-3", num_steps=200)
        studio = self.store.ingest_execution_trace(large)
        graph = DecisionGraphBuilder.build(studio)
        from backend.reasoning_studio.models import NodeType
        decision_nodes = [n for n in graph.nodes if n.node_type == NodeType.DECISION]
        self.assertGreaterEqual(len(decision_nodes), 200)
        # 199 edges connecting sequential decision nodes
        self.assertGreaterEqual(len(graph.edges), 199)

    def test_timeline_200_steps(self) -> None:
        """Timeline must have at least 200 events (one per step)."""
        large = make_large_trace("exec-large-4", num_steps=200)
        studio = self.store.ingest_execution_trace(large)
        timeline = TimelineReplayer.build_timeline(studio)
        self.assertGreaterEqual(len(timeline), 200)

    def test_step_by_step_200_steps_completes(self) -> None:
        """Step-by-step traversal must complete all 200 steps without error."""
        large = make_large_trace("exec-large-5", num_steps=200)
        studio = self.store.ingest_execution_trace(large)
        session = self.replay.create_session(studio.studio_trace_id)
        self.replay.start(session.session_id)
        count = 0
        while True:
            step = self.replay.next_step(session.session_id)
            if step is None:
                break
            count += 1
        self.assertEqual(count, 200)
