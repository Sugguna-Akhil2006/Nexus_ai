"""Per-execution span recorder that builds a complete ExecutionTrace."""

import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.observability.models import (
    ExecutionTrace,
    FailureRecord,
    KnowledgeSourceRef,
    MemoryAccess,
    PromptMetadata,
    ReasoningStep,
    ResponseMetadata,
    SpanStatus,
    TraceSpan,
)


class ExecutionTracer:
    """Records spans, reasoning steps, and accessors for a single execution.

    One ``ExecutionTracer`` is created per execution and discarded after
    ``build_trace`` is called.
    """

    def __init__(self, execution_id: str, workflow_id: str = "", workspace_id: str = "") -> None:
        self._lock = threading.Lock()
        self._execution_id = execution_id
        self._workflow_id = workflow_id
        self._workspace_id = workspace_id
        self._spans: Dict[str, TraceSpan] = {}
        self._span_start_times: Dict[str, float] = {}
        self._reasoning_steps: List[ReasoningStep] = []
        self._memory_accesses: List[MemoryAccess] = []
        self._knowledge_sources: List[KnowledgeSourceRef] = []
        self._failures: List[FailureRecord] = []
        self._agent_ids: List[str] = []
        self._modules: List[str] = []
        self._prompt_metadata: Optional[PromptMetadata] = None
        self._response_metadata: Optional[ResponseMetadata] = None
        self._wall_start = time.perf_counter()
        self._started_at = datetime.utcnow().isoformat()

    # ------------------------------------------------------------------
    # Span management
    # ------------------------------------------------------------------

    def start_span(
        self,
        name: str,
        module: str = "",
        parent_span_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Opens a new timed span and returns its ``span_id``."""
        span = TraceSpan(
            name=name,
            module=module,
            parent_span_id=parent_span_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._spans[span.span_id] = span
            self._span_start_times[span.span_id] = time.perf_counter()
            if module and module not in self._modules:
                self._modules.append(module)
        return span.span_id

    def end_span(
        self,
        span_id: str,
        status: SpanStatus = SpanStatus.COMPLETED,
        error: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Closes an open span, recording duration and final status."""
        with self._lock:
            span = self._spans.get(span_id)
            if span is None:
                return
            elapsed_ms = (time.perf_counter() - self._span_start_times.pop(span_id, 0)) * 1000
            span.status = status
            span.duration_ms = round(elapsed_ms, 3)
            span.ended_at = datetime.utcnow().isoformat()
            span.error = error
            if metadata:
                span.metadata.update(metadata)

    # ------------------------------------------------------------------
    # Supplemental data recording
    # ------------------------------------------------------------------

    def record_reasoning_step(self, step: ReasoningStep) -> None:
        """Appends a reasoning step to the trace."""
        with self._lock:
            self._reasoning_steps.append(step)

    def record_memory_access(self, access: MemoryAccess) -> None:
        """Appends a memory access event."""
        with self._lock:
            self._memory_accesses.append(access)

    def record_knowledge_source(self, ref: KnowledgeSourceRef) -> None:
        """Appends a knowledge source reference."""
        with self._lock:
            self._knowledge_sources.append(ref)

    def record_failure(self, record: FailureRecord) -> None:
        """Appends a failure record."""
        with self._lock:
            self._failures.append(record)

    def add_agent(self, agent_id: str) -> None:
        """Registers an agent ID participating in this execution."""
        with self._lock:
            if agent_id not in self._agent_ids:
                self._agent_ids.append(agent_id)

    def set_prompt_metadata(self, metadata: PromptMetadata) -> None:
        """Stores prompt metadata for the execution."""
        with self._lock:
            self._prompt_metadata = metadata

    def set_response_metadata(self, metadata: ResponseMetadata) -> None:
        """Stores response metadata for the execution."""
        with self._lock:
            self._response_metadata = metadata

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build_trace(self, status: SpanStatus = SpanStatus.COMPLETED) -> ExecutionTrace:
        """Constructs and returns the final immutable ``ExecutionTrace``.

        Args:
            status: The overall execution outcome status.

        Returns:
            A complete ``ExecutionTrace`` capturing all recorded data.
        """
        with self._lock:
            total_ms = round((time.perf_counter() - self._wall_start) * 1000, 3)
            return ExecutionTrace(
                execution_id=self._execution_id,
                workflow_id=self._workflow_id,
                workspace_id=self._workspace_id,
                agent_ids=list(self._agent_ids),
                modules_executed=list(self._modules),
                spans=list(self._spans.values()),
                reasoning_steps=list(self._reasoning_steps),
                memory_accesses=list(self._memory_accesses),
                knowledge_sources=list(self._knowledge_sources),
                prompt_metadata=self._prompt_metadata,
                response_metadata=self._response_metadata,
                started_at=self._started_at,
                ended_at=datetime.utcnow().isoformat(),
                total_duration_ms=total_ms,
                status=status,
            )
