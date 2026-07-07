"""Reasoning Studio API — unified developer-facing facade.

Coordinates trace ingestion, replay, graph building, evidence
visualisation, confidence analysis, trace comparison, timeline
construction, and explanation generation.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from backend.observability.models import ExecutionTrace
from backend.reasoning_studio.confidence_analyzer import ConfidenceAnalyzer
from backend.reasoning_studio.decision_graph import DecisionGraphBuilder
from backend.reasoning_studio.evidence_visualizer import EvidenceVisualizer
from backend.reasoning_studio.explanation_generator import ExplanationGenerator
from backend.reasoning_studio.models import (
    ConfidenceAnalysis,
    DecisionGraph,
    Explanation,
    EvidenceTree,
    ReplaySession,
    StudioTrace,
    TraceDiff,
)
from backend.reasoning_studio.reasoning_diff import ReasoningDiff
from backend.reasoning_studio.reasoning_replay import ReasoningReplay
from backend.reasoning_studio.reasoning_trace import ReasoningTrace
from backend.reasoning_studio.timeline_replayer import TimelineEvent, TimelineReplayer
from backend.reasoning_studio.trace_comparator import TraceComparator
from backend.runtime.event import EventBus


class StudioAPI:
    """Single entry-point for all Reasoning Studio operations.

    The Studio is **read-only with respect to intelligence execution**: it
    ingests already-completed ``ExecutionTrace`` objects from the Observability
    layer and provides replay, graph, diff, and explanation capabilities
    without touching workflow or agent execution paths.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._lock = threading.RLock()
        bus = event_bus or EventBus()
        self._trace_store = ReasoningTrace(event_bus=bus)
        self._replay_engine = ReasoningReplay(self._trace_store, event_bus=bus)
        self._comparator = TraceComparator(self._trace_store, event_bus=bus)
        self._explainer = ExplanationGenerator(event_bus=bus)

    # ------------------------------------------------------------------
    # Trace ingestion
    # ------------------------------------------------------------------

    def ingest(self, execution_trace: ExecutionTrace) -> StudioTrace:
        """Ingests an ``ExecutionTrace`` from Observability and stores a Studio trace.

        Args:
            execution_trace: A completed trace from ``TelemetryManager``.

        Returns:
            The resulting ``StudioTrace``.
        """
        with self._lock:
            return self._trace_store.ingest_execution_trace(execution_trace)

    def get_trace(self, studio_trace_id: str) -> Optional[StudioTrace]:
        """Returns a Studio trace by ID."""
        return self._trace_store.get_trace(studio_trace_id)

    def get_trace_by_execution(self, execution_id: str) -> Optional[StudioTrace]:
        """Returns the Studio trace for the given original execution ID."""
        return self._trace_store.get_trace_by_execution(execution_id)

    def list_traces(self) -> List[StudioTrace]:
        """Lists all stored Studio traces."""
        return self._trace_store.list_traces()

    # ------------------------------------------------------------------
    # Replay API
    # ------------------------------------------------------------------

    def create_replay_session(self, studio_trace_id: str) -> ReplaySession:
        """Creates a step-by-step replay session."""
        return self._replay_engine.create_session(studio_trace_id)

    def replay_start(self, session_id: str) -> ReplaySession:
        """Starts or resumes a replay session."""
        return self._replay_engine.start(session_id)

    def replay_pause(self, session_id: str) -> ReplaySession:
        """Pauses a running replay session."""
        return self._replay_engine.pause(session_id)

    def replay_jump_to(self, session_id: str, step_index: int) -> ReplaySession:
        """Jumps the replay cursor to a specific step."""
        return self._replay_engine.jump_to(session_id, step_index)

    def replay_next_step(self, session_id: str):  # type: ignore[return]
        """Advances the replay by one step and returns it."""
        return self._replay_engine.next_step(session_id)

    def replay_all(self, studio_trace_id: str) -> List:
        """Returns all steps of a trace in order (full replay)."""
        return self._replay_engine.replay_all(studio_trace_id)

    # ------------------------------------------------------------------
    # Decision graph
    # ------------------------------------------------------------------

    def get_decision_graph(self, studio_trace_id: str) -> DecisionGraph:
        """Builds and returns the decision / evidence graph for a trace."""
        trace = self._require_trace(studio_trace_id)
        return DecisionGraphBuilder.build(trace)

    # ------------------------------------------------------------------
    # Evidence visualizer
    # ------------------------------------------------------------------

    def get_evidence_tree(
        self,
        studio_trace_id: str,
        execution_trace: ExecutionTrace,
    ) -> EvidenceTree:
        """Builds an evidence tree combining Studio and Observability data."""
        trace = self._require_trace(studio_trace_id)
        return EvidenceVisualizer.build_tree(trace, execution_trace)

    # ------------------------------------------------------------------
    # Confidence analysis
    # ------------------------------------------------------------------

    def get_confidence_analysis(self, studio_trace_id: str) -> ConfidenceAnalysis:
        """Returns the confidence evolution analysis for a trace."""
        trace = self._require_trace(studio_trace_id)
        return ConfidenceAnalyzer.analyze(trace)

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def get_timeline(self, studio_trace_id: str) -> List[TimelineEvent]:
        """Returns the chronological timeline of events for a trace."""
        trace = self._require_trace(studio_trace_id)
        return TimelineReplayer.build_timeline(trace)

    # ------------------------------------------------------------------
    # Trace comparison / diff
    # ------------------------------------------------------------------

    def compare_traces(
        self,
        left_trace_id: str,
        right_trace_id: str,
    ) -> TraceDiff:
        """Compares two Studio traces and publishes the diff event."""
        return self._comparator.compare(left_trace_id, right_trace_id)

    # ------------------------------------------------------------------
    # Explanation
    # ------------------------------------------------------------------

    def get_explanation(self, studio_trace_id: str) -> Explanation:
        """Generates human-readable explanations for all why-* questions."""
        trace = self._require_trace(studio_trace_id)
        return self._explainer.generate(trace)

    # ------------------------------------------------------------------
    # Developer console display
    # ------------------------------------------------------------------

    def get_console_display_data(self, studio_trace_id: str) -> Dict[str, Any]:
        """Compiles all developer-console panels for one trace.

        Returns a single dict containing:
          - ``timeline`` — list of chronological events
          - ``decision_graph`` — serialised graph (nodes + edges counts)
          - ``confidence_analysis`` — evolution summary
          - ``explanation`` — human-readable why-* answers
          - ``trace_summary`` — key trace fields
        """
        trace = self._require_trace(studio_trace_id)

        timeline = TimelineReplayer.build_timeline(trace)
        graph = DecisionGraphBuilder.build(trace)
        conf = ConfidenceAnalyzer.analyze(trace)
        explanation = self._explainer.generate(trace)

        return {
            "trace_summary": {
                "studio_trace_id": trace.studio_trace_id,
                "execution_id": trace.execution_id,
                "workflow_id": trace.workflow_id,
                "total_steps": trace.total_steps,
                "final_confidence": trace.final_confidence,
                "created_at": trace.created_at,
            },
            "timeline": [
                {
                    "timestamp": e.timestamp,
                    "event_kind": e.event_kind,
                    "step_index": e.step_index,
                    "label": e.label,
                }
                for e in timeline
            ],
            "decision_graph": {
                "graph_id": graph.graph_id,
                "node_count": len(graph.nodes),
                "edge_count": len(graph.edges),
            },
            "confidence_analysis": {
                "min": conf.min_confidence,
                "max": conf.max_confidence,
                "average": conf.average_confidence,
                "drops_at_steps": conf.drops,
                "peaks_at_steps": conf.peaks,
            },
            "explanation": {
                "why_this_decision": explanation.why_this_decision,
                "why_this_provider": explanation.why_this_provider,
                "why_this_workflow": explanation.why_this_workflow,
                "why_this_confidence": explanation.why_this_confidence,
                "summary": explanation.summary,
            },
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_trace(self, studio_trace_id: str) -> StudioTrace:
        trace = self._trace_store.get_trace(studio_trace_id)
        if trace is None:
            raise ValueError(f"Studio trace '{studio_trace_id}' not found.")
        return trace
