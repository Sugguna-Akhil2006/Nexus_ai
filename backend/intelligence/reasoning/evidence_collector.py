"""Collects, filters, and ranks incoming evidence facts by relevance."""

import re
from typing import List, Dict, Any
from backend.intelligence.reasoning.models import Evidence
from backend.intelligence.reasoning.reasoning_context import ReasoningContext


class EvidenceCollector:
    """Filters low-confidence noise and ranks evidence facts by keyword overlap."""

    def collect_and_rank_evidence(
        self,
        query: str,
        sources: List[Evidence],
        ctx: ReasoningContext
    ) -> List[Evidence]:
        """Filters, ranks, and logs evidence items relative to the query."""
        ctx.add_trace(f"Starting evidence collection over {len(sources)} input records.")
        
        # 1. Filter out empty or extremely low confidence evidence
        filtered = []
        for ev in sources:
            if not ev.fact.strip():
                continue
            if ev.confidence < 0.1:
                ctx.add_trace(f"Filtered out low confidence noise: '{ev.fact[:40]}...' (Conf: {ev.confidence})")
                continue
            filtered.append(ev)

        # 2. Tokenize query words to calculate relevance
        query_words = set(re.findall(r"\b\w{3,15}\b", query.lower()))
        
        # 3. Compute relevance scores and sort
        scored_evidence = []
        for ev in filtered:
            fact_words = set(re.findall(r"\b\w{3,15}\b", ev.fact.lower()))
            overlap = len(query_words & fact_words)
            
            # Score: relevance weight + confidence weight
            relevance_score = float(overlap) * 0.5 + ev.confidence
            scored_evidence.append((ev, relevance_score))

        # Sort by score descending
        scored_evidence.sort(key=lambda x: x[1], reverse=True)
        ranked_evidence = [item[0] for item in scored_evidence]
        
        ctx.add_trace(f"Collected and ranked {len(ranked_evidence)} relevant evidence items.")
        return ranked_evidence
