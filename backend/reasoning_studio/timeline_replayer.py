"""Timeline replayer — ordered, timestamp-sorted event stream for a Studio trace."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List

from backend.reasoning_studio.models import CapturedReasoningStep, StudioTrace


@dataclass(frozen=True)
class TimelineEvent:
    """A single chronological event emitted during a timeline replay."""

    timestamp: str
    event_kind: str           # "step" | "tool_call" | "memory_lookup" | "knowledge_query"
    step_index: int
    step_id: str
    label: str
    metadata: Dict[str, Any]


class TimelineReplayer:
    """Flattens a Studio trace into a chronological event stream.

    Useful for the developer console's *Reasoning Timeline* panel: it
    interleaves reasoning steps with their child events (tool calls,
    memory lookups, knowledge queries) in the order they were originally
    produced, enabling a rich step-by-step timeline view.
    """

    @staticmethod
    def build_timeline(trace: StudioTrace) -> List[TimelineEvent]:
        """Produces a sorted list of ``TimelineEvent`` objects for the trace.

        Args:
            trace: The ``StudioTrace`` to process.

        Returns:
            Flat list of timeline events in timestamp-ascending order.
        """
        events: List[TimelineEvent] = []

        for step in trace.steps:
            # ── Main reasoning step event ──────────────────────────────
            events.append(TimelineEvent(
                timestamp=step.timestamp,
                event_kind="step",
                step_index=step.sequence_index,
                step_id=step.step_id,
                label=step.description,
                metadata={
                    "confidence": step.confidence,
                    "prompt_version": step.prompt_version,
                    "provider": step.provider_response_summary,
                },
            ))

            # ── Tool invocations ──────────────────────────────────────
            for tool in step.tool_invocations:
                events.append(TimelineEvent(
                    timestamp=step.timestamp,
                    event_kind="tool_call",
                    step_index=step.sequence_index,
                    step_id=step.step_id,
                    label=f"Tool: {tool}",
                    metadata={"tool": tool},
                ))

            # ── Memory lookups ─────────────────────────────────────────
            for ml in step.memory_lookups:
                events.append(TimelineEvent(
                    timestamp=step.timestamp,
                    event_kind="memory_lookup",
                    step_index=step.sequence_index,
                    step_id=step.step_id,
                    label=f"Memory: {ml}",
                    metadata={"lookup": ml},
                ))

            # ── Knowledge queries ──────────────────────────────────────
            for kq in step.knowledge_queries:
                events.append(TimelineEvent(
                    timestamp=step.timestamp,
                    event_kind="knowledge_query",
                    step_index=step.sequence_index,
                    step_id=step.step_id,
                    label=f"Knowledge: {kq}",
                    metadata={"query": kq},
                ))

        # Sort by timestamp string (ISO-8601 lexicographic order is correct)
        events.sort(key=lambda e: e.timestamp)
        return events

    @staticmethod
    def iter_timeline(trace: StudioTrace) -> Iterator[TimelineEvent]:
        """Lazy iterator version of ``build_timeline`` for memory-efficient streaming."""
        yield from TimelineReplayer.build_timeline(trace)
