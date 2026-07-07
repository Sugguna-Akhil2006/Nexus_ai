"""Confidence analyzer — tracks confidence evolution over reasoning steps."""

from __future__ import annotations

from typing import List

from backend.reasoning_studio.models import (
    ConfidenceAnalysis,
    ConfidencePoint,
    StudioTrace,
)


class ConfidenceAnalyzer:
    """Analyses confidence deltas across a trace to surface drops and peaks."""

    @staticmethod
    def analyze(trace: StudioTrace) -> ConfidenceAnalysis:
        """Computes the confidence timeline and identifies notable events.

        Args:
            trace: The ``StudioTrace`` to analyse.

        Returns:
            A fully populated ``ConfidenceAnalysis``.
        """
        timeline: List[ConfidencePoint] = []
        drops: List[int] = []
        peaks: List[int] = []

        prev_confidence: float | None = None

        for step in trace.steps:
            point = ConfidencePoint(
                step_index=step.sequence_index,
                step_id=step.step_id,
                description=step.description,
                confidence=step.confidence,
                timestamp=step.timestamp,
            )
            timeline.append(point)

            if prev_confidence is not None:
                if step.confidence < prev_confidence - 0.05:   # notable drop
                    drops.append(step.sequence_index)
                elif step.confidence > prev_confidence + 0.05:  # notable peak
                    peaks.append(step.sequence_index)

            prev_confidence = step.confidence

        confidences = [p.confidence for p in timeline]
        min_conf = min(confidences) if confidences else 0.0
        max_conf = max(confidences) if confidences else 0.0
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return ConfidenceAnalysis(
            studio_trace_id=trace.studio_trace_id,
            timeline=timeline,
            min_confidence=min_conf,
            max_confidence=max_conf,
            average_confidence=round(avg_conf, 4),
            drops=drops,
            peaks=peaks,
        )
