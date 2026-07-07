"""Trace comparator — compares two traces and publishes a diff event."""

from __future__ import annotations

from typing import Optional

from backend.reasoning_studio.models import TraceDiff
from backend.reasoning_studio.reasoning_diff import ReasoningDiff
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class TraceComparator:
    """Compares two Studio traces by their IDs and publishes ``reasoning.compared``.

    Delegates the actual diff logic to ``ReasoningDiff`` to keep this class
    focused solely on orchestration and event emission.
    """

    def __init__(
        self,
        trace_store: ReasoningTrace,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._store = trace_store
        self._event_bus = event_bus or EventBus()

    def compare(
        self,
        left_trace_id: str,
        right_trace_id: str,
    ) -> TraceDiff:
        """Compares two traces and publishes the diff result.

        Args:
            left_trace_id:  ID of the baseline ``StudioTrace``.
            right_trace_id: ID of the trace being compared.

        Returns:
            A fully computed ``TraceDiff``.

        Raises:
            ValueError: If either trace ID is not found in the store.
        """
        left = self._store.get_trace(left_trace_id)
        right = self._store.get_trace(right_trace_id)

        if left is None:
            raise ValueError(f"Left trace '{left_trace_id}' not found.")
        if right is None:
            raise ValueError(f"Right trace '{right_trace_id}' not found.")

        diff = ReasoningDiff.diff(left, right)

        self._event_bus.publish(Event(
            event_type=EventType.REASONING_COMPARED,
            priority=EventPriority.NORMAL,
            payload={
                "diff_id": diff.diff_id,
                "left_trace_id": left_trace_id,
                "right_trace_id": right_trace_id,
                "total_changed": diff.total_changed,
                "similarity_score": diff.similarity_score,
            },
        ))

        return diff
