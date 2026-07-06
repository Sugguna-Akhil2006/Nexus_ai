"""Thread-safe registry managing active and completed execution tracers."""

import threading
from datetime import datetime
from typing import Dict, List, Optional

from backend.runtime.event import Event, EventBus, EventType
from backend.observability.execution_trace import ExecutionTracer
from backend.observability.models import ExecutionTrace, SpanStatus


class TraceManager:
    """Manages the lifecycle of ``ExecutionTracer`` instances.

    Maintains a registry of active tracers and a finalized trace store.
    Publishes ``trace.completed`` on the EventBus when a trace is finalized.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active: Dict[str, ExecutionTracer] = {}
        self._completed: Dict[str, ExecutionTrace] = {}
        self._event_bus = EventBus()

    # ------------------------------------------------------------------
    # Tracer lifecycle
    # ------------------------------------------------------------------

    def start_trace(
        self,
        execution_id: str,
        workflow_id: str = "",
        workspace_id: str = "",
    ) -> ExecutionTracer:
        """Creates and registers a new ``ExecutionTracer`` for ``execution_id``.

        Args:
            execution_id: Unique identifier for this execution.
            workflow_id: Associated workflow ID (if applicable).
            workspace_id: Workspace context identifier.

        Returns:
            The newly created ``ExecutionTracer``.
        """
        tracer = ExecutionTracer(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workspace_id=workspace_id,
        )
        with self._lock:
            self._active[execution_id] = tracer
        return tracer

    def get_tracer(self, execution_id: str) -> Optional[ExecutionTracer]:
        """Returns the active tracer for ``execution_id``, or ``None``."""
        with self._lock:
            return self._active.get(execution_id)

    def end_trace(
        self,
        execution_id: str,
        status: SpanStatus = SpanStatus.COMPLETED,
    ) -> Optional[ExecutionTrace]:
        """Finalises the active tracer, persists the trace, and publishes an event.

        Args:
            execution_id: The execution whose tracer should be finalized.
            status: Overall execution outcome.

        Returns:
            The completed ``ExecutionTrace``, or ``None`` if not found.
        """
        with self._lock:
            tracer = self._active.pop(execution_id, None)

        if tracer is None:
            return None

        trace = tracer.build_trace(status=status)
        with self._lock:
            self._completed[execution_id] = trace

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="TraceManager",
            payload={
                "event": "trace.completed",
                "execution_id": execution_id,
                "trace_id": trace.trace_id,
                "status": status.value,
                "duration_ms": trace.total_duration_ms,
                "timestamp": datetime.utcnow().isoformat(),
            },
        ))
        return trace

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_trace(self, execution_id: str) -> Optional[ExecutionTrace]:
        """Returns a completed trace by execution ID."""
        with self._lock:
            return self._completed.get(execution_id)

    def list_traces(self) -> List[ExecutionTrace]:
        """Returns all finalized traces."""
        with self._lock:
            return list(self._completed.values())
