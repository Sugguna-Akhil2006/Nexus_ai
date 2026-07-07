"""Compiles structured conclusions and reasoning trace maps."""

from typing import List, Dict, Any
from backend.intelligence.reasoning.models import Evidence, Conflict
from backend.intelligence.reasoning.reasoning_context import ReasoningContext


class ResponsePlanner:
    """Summarizes fused facts in context of the query to compile conclusion lists."""

    def compile_conclusions(
        self,
        query: str,
        fused_evidence: List[Evidence],
        conflicts: List[Conflict],
        ctx: ReasoningContext
    ) -> List[str]:
        """Translates final evidence and conflict pools into concluding assertions."""
        ctx.add_trace("Compiling final structured conclusions.")
        conclusions = []

        # 1. Map top relevant facts as core conclusions
        for idx, ev in enumerate(fused_evidence[:3]):
            conclusions.append(f"Derived conclusion from {ev.source}: {ev.fact}")

        # 2. Add alerts if contradictions are present
        contradictions = [c for c in conflicts if c.category == "Contradictory Sources"]
        if contradictions:
            conclusions.append(
                f"Attention: Detected {len(contradictions)} conflicting source assertions regarding query topics."
            )

        # 3. Handle empty case
        if not conclusions:
            conclusions.append("Unable to derive firm conclusions due to lack of supporting evidence.")

        ctx.add_trace(f"Compiled {len(conclusions)} conclusions.")
        return conclusions
