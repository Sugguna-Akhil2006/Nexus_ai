"""Evaluates consensus weights and resolves duplicates using the Unified Reasoning Engine."""

from typing import List, Dict, Any
from backend.intelligence.reasoning.models import Evidence, ReasoningRequest
from backend.intelligence.reasoning.reasoning_engine import UnifiedReasoningEngine
from backend.intelligence.collaboration.shared_context import SharedContext


class ConsensusEngine:
    """Invokes central reasoning processes to resolve consensus and detect overlaps."""

    def __init__(self) -> None:
        self.reasoning_engine = UnifiedReasoningEngine()

    def build_consensus(
        self,
        workspace_id: str,
        objective: str,
        context: SharedContext
    ) -> Any:
        """Translates context evidence into ReasoningRequest and executes the pipeline."""
        raw_evidence = context.get_evidence()
        
        evidence_list = []
        for idx, item in enumerate(raw_evidence):
            evidence_list.append(Evidence(
                evidence_id=f"ev-collab-{idx}",
                source=item["source"],
                fact=item["fact"],
                confidence=item["confidence"]
            ))

        req = ReasoningRequest(
            workspace_id=workspace_id,
            query=objective,
            sources=evidence_list
        )
        # Execute reasoning
        return self.reasoning_engine.execute_reasoning(req)
