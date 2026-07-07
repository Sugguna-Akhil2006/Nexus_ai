"""Reasoning trace store — enriches raw ExecutionTraces for the Studio.

Does NOT re-collect telemetry.  It ingests already-completed
``ExecutionTrace`` objects from the Observability layer and converts
them into ``StudioTrace`` + ``CapturedReasoningStep`` artefacts.
"""

from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional

from backend.observability.models import ExecutionTrace
from backend.reasoning_studio.models import CapturedReasoningStep, StudioTrace
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class ReasoningTrace:
    """Thread-safe registry of Studio traces built from Observability data.

    Args:
        event_bus: Optional EventBus override (useful in tests).
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._lock = threading.RLock()
        self._traces: Dict[str, StudioTrace] = {}          # studio_trace_id → StudioTrace
        self._by_execution: Dict[str, str] = {}            # execution_id    → studio_trace_id
        self._event_bus = event_bus or EventBus()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def ingest_execution_trace(self, trace: ExecutionTrace) -> StudioTrace:
        """Converts an ``ExecutionTrace`` into a ``StudioTrace`` and stores it.

        Args:
            trace: A completed trace from the Observability Platform.

        Returns:
            The newly created ``StudioTrace``.
        """
        steps: List[CapturedReasoningStep] = []

        for idx, rs in enumerate(trace.reasoning_steps):
            # Collect memory lookups that occurred in this step's span window
            memory_lookups = [
                f"{ma.operation}:{ma.key}"
                for ma in trace.memory_accesses
                if ma.timestamp >= rs.timestamp
            ]

            # Collect knowledge queries
            knowledge_queries = [
                f"{ks.source_type}:{ks.identifier}"
                for ks in trace.knowledge_sources
                if ks.timestamp >= rs.timestamp
            ]

            crs = CapturedReasoningStep(
                source_step_id=rs.step_id,
                execution_id=trace.execution_id,
                description=rs.description,
                inputs=rs.inputs,
                outputs=rs.outputs,
                confidence=rs.confidence,
                prompt_version=trace.prompt_metadata.template_name if trace.prompt_metadata else "",
                provider_response_summary=(
                    f"{trace.prompt_metadata.provider}/{trace.prompt_metadata.model}"
                    if trace.prompt_metadata else ""
                ),
                memory_lookups=memory_lookups[:5],     # cap for display
                knowledge_queries=knowledge_queries[:5],
                sequence_index=idx,
            )
            steps.append(crs)

        final_confidence = steps[-1].confidence if steps else 0.0

        studio_trace = StudioTrace(
            execution_id=trace.execution_id,
            workflow_id=trace.workflow_id,
            workspace_id=trace.workspace_id,
            steps=steps,
            total_steps=len(steps),
            final_confidence=final_confidence,
        )

        with self._lock:
            self._traces[studio_trace.studio_trace_id] = studio_trace
            self._by_execution[trace.execution_id] = studio_trace.studio_trace_id

        self._event_bus.publish(Event(
            event_type=EventType.REASONING_TRACE_CREATED,
            priority=EventPriority.NORMAL,
            payload={
                "studio_trace_id": studio_trace.studio_trace_id,
                "execution_id": trace.execution_id,
                "total_steps": len(steps),
            },
        ))

        return studio_trace

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_trace(self, studio_trace_id: str) -> Optional[StudioTrace]:
        """Returns a Studio trace by its ID."""
        with self._lock:
            return self._traces.get(studio_trace_id)

    def get_trace_by_execution(self, execution_id: str) -> Optional[StudioTrace]:
        """Returns the Studio trace for the given execution ID."""
        with self._lock:
            tid = self._by_execution.get(execution_id)
            return self._traces.get(tid) if tid else None

    def list_traces(self) -> List[StudioTrace]:
        """Returns all stored Studio traces."""
        with self._lock:
            return list(self._traces.values())
