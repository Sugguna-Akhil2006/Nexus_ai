"""Computes reasoning confidence scores, applying penalties for conflicts and gaps."""

from typing import List
from backend.intelligence.reasoning.models import Evidence, Conflict
from backend.intelligence.reasoning.reasoning_context import ReasoningContext


class ConfidenceEngine:
    """Calculates overall composite confidence ratings adjusting for pipeline anomalies."""

    def compute_overall_confidence(
        self,
        evidence: List[Evidence],
        conflicts: List[Conflict],
        ctx: ReasoningContext
    ) -> float:
        """Estimates final reasoning confidence score with penalty adjustments."""
        if not evidence:
            ctx.add_trace("Confidence set to 0.0 due to empty evidence pool.")
            return 0.0

        # 1. Start with average confidence of evidence
        total_conf = sum(ev.confidence for ev in evidence)
        base_avg = total_conf / len(evidence)

        # 2. Subtract penalties based on detected conflict severity
        penalty = 0.0
        for c in conflicts:
            if c.severity == "High":
                penalty += 0.15
            elif c.severity == "Medium":
                penalty += 0.08
            elif c.severity == "Low":
                penalty += 0.03

        final_conf = max(0.1, min(1.0, base_avg - penalty))
        final_conf = round(final_conf, 2)
        
        ctx.add_trace(f"Calculated composite confidence score: {final_conf} (Base: {round(base_avg, 2)}, Penalty: {round(penalty, 2)})")
        return final_conf
