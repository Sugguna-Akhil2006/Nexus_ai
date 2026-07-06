"""Delegates fusion, conflict checks, and confidence calculations to the Unified Reasoning Engine."""

from typing import List, Dict, Any
from backend.intelligence.reasoning.models import ReasoningRequest
from backend.intelligence.reasoning.reasoning_engine import UnifiedReasoningEngine
from backend.intelligence.reasoning.models import Evidence


class ResultMerger:
    """Merges cross-module outputs using the central Reasoning Engine."""

    def __init__(self) -> None:
        self.reasoning_engine = UnifiedReasoningEngine()

    def merge_results(
        self,
        workspace_id: str,
        query: str,
        evidence: List[Evidence],
        options: Dict[str, Any]
    ) -> Any:
        """Executes the Unified Reasoning Engine pipeline over collected evidence."""
        req = ReasoningRequest(
            workspace_id=workspace_id,
            query=query,
            sources=evidence,
            options=options
        )
        return self.reasoning_engine.execute_reasoning(req)
