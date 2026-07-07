"""Tests for trace ingestion and Studio trace storage."""

import unittest

from backend.observability.models import (
    ExecutionTrace,
    KnowledgeSourceRef,
    MemoryAccess,
    PromptMetadata,
    ReasoningStep,
    SpanStatus,
)
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.runtime.event import EventBus


def _reset_bus() -> None:
    bus = EventBus()
    with bus._lock:
        bus._subscribers.clear()
        bus._queue.clear()
        bus._history.clear()
        bus._statistics = {"published_count": 0, "dispatched_count": 0, "failed_count": 0, "by_type": {}}


def make_execution_trace(
    execution_id: str = "exec-001",
    workflow_id: str = "wf-test",
    num_steps: int = 3,
    status: SpanStatus = SpanStatus.COMPLETED,
) -> ExecutionTrace:
    """Builds a minimal ExecutionTrace with synthetic reasoning steps."""
    steps = [
        ReasoningStep(
            description=f"Step {i}: analyse inputs",
            inputs={"x": i},
            outputs={"result": i * 2},
            confidence=0.7 + i * 0.05,
        )
        for i in range(num_steps)
    ]
    trace = ExecutionTrace(
        execution_id=execution_id,
        workflow_id=workflow_id,
        workspace_id="ws-test",
        reasoning_steps=steps,
        status=status,
        prompt_metadata=PromptMetadata(
            template_name="v1.2",
            model="gpt-4o",
            provider="openai",
            token_count=300,
        ),
        knowledge_sources=[
            KnowledgeSourceRef(
                source_type="document",
                identifier="doc-alpha",
                relevance_score=0.85,
            )
        ],
        memory_accesses=[
            MemoryAccess(operation="read", key="user_context", namespace="session"),
        ],
    )
    trace.total_duration_ms = 1500.0
    return trace


class TestReasoningTrace(unittest.TestCase):
    """Validates trace ingestion, retrieval, and step enrichment."""

    def setUp(self) -> None:
        _reset_bus()
        self.store = ReasoningTrace()

    def test_ingest_creates_studio_trace(self) -> None:
        """Ingesting an ExecutionTrace must produce a StudioTrace with correct fields."""
        exec_trace = make_execution_trace(num_steps=3)
        studio = self.store.ingest_execution_trace(exec_trace)

        self.assertEqual(studio.execution_id, "exec-001")
        self.assertEqual(studio.workflow_id, "wf-test")
        self.assertEqual(studio.total_steps, 3)
        self.assertGreaterEqual(studio.final_confidence, 0.7)

    def test_get_by_execution_id(self) -> None:
        """Trace should be retrievable by original execution ID."""
        exec_trace = make_execution_trace(execution_id="exec-xyz")
        studio = self.store.ingest_execution_trace(exec_trace)

        retrieved = self.store.get_trace_by_execution("exec-xyz")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.studio_trace_id, studio.studio_trace_id)

    def test_prompt_version_captured(self) -> None:
        """Steps should carry the prompt version from PromptMetadata."""
        exec_trace = make_execution_trace()
        studio = self.store.ingest_execution_trace(exec_trace)
        for step in studio.steps:
            self.assertEqual(step.prompt_version, "v1.2")

    def test_list_traces(self) -> None:
        """All ingested traces must appear in list_traces()."""
        for i in range(4):
            self.store.ingest_execution_trace(
                make_execution_trace(execution_id=f"exec-{i}", workflow_id="wf-list")
            )
        traces = self.store.list_traces()
        self.assertEqual(len(traces), 4)

    def test_unknown_trace_returns_none(self) -> None:
        """Querying a non-existent ID must return None safely."""
        self.assertIsNone(self.store.get_trace("non-existent-id"))
