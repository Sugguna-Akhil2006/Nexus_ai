"""Explanation generator — produces human-readable rationales for reasoning artefacts."""

from __future__ import annotations

from typing import Optional

from backend.reasoning_studio.confidence_analyzer import ConfidenceAnalyzer
from backend.reasoning_studio.models import Explanation, StudioTrace
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class ExplanationGenerator:
    """Generates human-readable explanations of a reasoning trace.

    Answers the four core developer questions:
      - Why this decision?
      - Why this provider?
      - Why this workflow?
      - Why this confidence?

    Publishes ``reasoning.validated`` when an explanation is produced,
    signalling that the trace has been reviewed/explained.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._event_bus = event_bus or EventBus()

    def generate(self, trace: StudioTrace) -> Explanation:
        """Generates a full explanation for the given trace.

        Args:
            trace: The ``StudioTrace`` to explain.

        Returns:
            An ``Explanation`` model with populated narrative fields.
        """
        conf_analysis = ConfidenceAnalyzer.analyze(trace)

        # ── Why this decision? ────────────────────────────────────────
        step_count = trace.total_steps
        if step_count == 0:
            why_decision = "No reasoning steps were captured for this trace."
        else:
            last_step = trace.steps[-1]
            why_decision = (
                f"The final decision was reached after {step_count} reasoning step(s). "
                f"The last step — '{last_step.description}' — produced the terminal "
                f"conclusion with a confidence of {last_step.confidence:.2f}."
            )
            if last_step.intermediate_conclusions:
                why_decision += (
                    f" Key intermediate conclusions: "
                    + "; ".join(last_step.intermediate_conclusions[:3]) + "."
                )

        # ── Why this provider? ────────────────────────────────────────
        providers = list({
            step.provider_response_summary
            for step in trace.steps
            if step.provider_response_summary
        })
        if providers:
            why_provider = (
                f"The following provider(s) were used: {', '.join(providers)}. "
                "Provider selection is governed by the active Connector Framework "
                "policy (cost, latency, and capability requirements)."
            )
        else:
            why_provider = "No provider metadata was captured for this trace."

        # ── Why this workflow? ────────────────────────────────────────
        why_workflow = (
            f"Workflow '{trace.workflow_id}' was selected by the Workflow Engine "
            f"based on the workspace context '{trace.workspace_id}'. "
            f"The workflow orchestrated {step_count} reasoning step(s)."
        )

        # ── Why this confidence? ──────────────────────────────────────
        avg_conf = conf_analysis.average_confidence
        drops = conf_analysis.drops
        peaks = conf_analysis.peaks

        why_confidence = (
            f"The overall average confidence across all steps was {avg_conf:.2f}. "
        )
        if drops:
            why_confidence += (
                f"Confidence dropped at step(s) {drops} — these may indicate "
                "ambiguous evidence or conflicting knowledge sources. "
            )
        if peaks:
            why_confidence += (
                f"Confidence peaked at step(s) {peaks} — likely where strong "
                "corroborating evidence was found. "
            )
        if not drops and not peaks:
            why_confidence += "Confidence remained stable throughout the trace."

        # ── Summary ───────────────────────────────────────────────────
        summary = (
            f"Trace '{trace.studio_trace_id}' for workflow '{trace.workflow_id}' "
            f"completed {step_count} reasoning step(s) with a final confidence of "
            f"{trace.final_confidence:.2f} and an average confidence of {avg_conf:.2f}."
        )

        explanation = Explanation(
            studio_trace_id=trace.studio_trace_id,
            why_this_decision=why_decision,
            why_this_provider=why_provider,
            why_this_workflow=why_workflow,
            why_this_confidence=why_confidence,
            summary=summary,
        )

        self._event_bus.publish(Event(
            event_type=EventType.REASONING_VALIDATED,
            priority=EventPriority.NORMAL,
            payload={
                "explanation_id": explanation.explanation_id,
                "studio_trace_id": trace.studio_trace_id,
                "avg_confidence": avg_conf,
            },
        ))

        return explanation
