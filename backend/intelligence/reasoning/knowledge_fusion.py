"""Synthesizes overlapping evidence nodes into singular unified statements."""

import re
from typing import List, Dict, Set
from backend.intelligence.reasoning.models import Evidence
from backend.intelligence.reasoning.reasoning_context import ReasoningContext


class KnowledgeFuser:
    """Synthesizes duplicate concepts and groups matching evidence logs."""

    def fuse_knowledge(
        self,
        evidence: List[Evidence],
        ctx: ReasoningContext
    ) -> List[Evidence]:
        """Combines closely related facts, merging source tracking and confidence.

        Iterates and groups any facts with Jaccard word overlaps > 0.75.
        """
        ctx.add_trace("Starting knowledge fusion synthesis.")
        if not evidence:
            return []

        fused: List[Evidence] = []
        visited = set()

        for i in range(len(evidence)):
            if i in visited:
                continue
            
            curr = evidence[i]
            visited.add(i)
            
            # Words in current fact
            w1 = set(re.findall(r"\w+", curr.fact.lower()))
            
            # Group all duplicate matches
            group = [curr]
            for j in range(i + 1, len(evidence)):
                if j in visited:
                    continue
                w2 = set(re.findall(r"\w+", evidence[j].fact.lower()))
                
                intersection = len(w1 & w2)
                union = len(w1 | w2)
                jaccard = (intersection / union) if union > 0 else 0.0
                
                if jaccard > 0.75:
                    group.append(evidence[j])
                    visited.add(j)

            if len(group) == 1:
                fused.append(curr)
            else:
                # Perform fusion merge
                # Pick the longest/most detailed fact text
                best_fact = max(group, key=lambda x: len(x.fact)).fact
                
                # Combine source names
                sources = list(set(g.source for g in group))
                source_str = " & ".join(sources)
                
                # Max confidence score
                max_conf = max(g.confidence for g in group)
                
                # Union metadata keys
                meta = {}
                for g in group:
                    meta.update(g.metadata)
                
                fused_item = Evidence(
                    evidence_id=curr.evidence_id,
                    source=source_str,
                    fact=best_fact,
                    confidence=max_conf,
                    metadata=meta
                )
                fused.append(fused_item)
                ctx.add_trace(f"Fused {len(group)} duplicate items into: '{best_fact[:40]}...' (Sources: {sources})")

        ctx.add_trace(f"Knowledge fusion complete. Synthesized {len(fused)} unique statements.")
        return fused
