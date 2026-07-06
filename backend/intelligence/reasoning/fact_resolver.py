"""Scans evidence logs for contradictions, duplicates, low confidence, and missing facts."""

import re
import uuid
from typing import List, Dict, Set, Any
from backend.intelligence.reasoning.models import Evidence, Conflict
from backend.intelligence.reasoning.reasoning_context import ReasoningContext


class FactResolver:
    """Detects and highlights structural discrepancies in the collected evidence."""

    def detect_conflicts(
        self,
        query: str,
        evidence: List[Evidence],
        ctx: ReasoningContext
    ) -> List[Conflict]:
        """Identifies conflicting facts, duplicates, low confidence, and missing evidence."""
        ctx.add_trace("Starting conflict and anomaly detection checks.")
        conflicts = []

        # 1. Check for missing evidence (query keywords completely absent from all facts)
        query_words = {w.lower() for w in re.findall(r"\b\w{4,15}\b", query) if w.lower() not in (
            "what", "where", "when", "which", "does", "have", "with", "from", "show", "list",
            "know", "knows", "affect", "affecting", "does", "doing", "uses", "user", "here", "there", "them", "their", "about", "query"
        )}
        
        all_fact_words = set()
        for ev in evidence:
            all_fact_words.update(re.findall(r"\b\w+\b", ev.fact.lower()))

        missing_keywords = query_words - all_fact_words
        if missing_keywords:
            conflicts.append(Conflict(
                conflict_id=f"cf-miss-{str(uuid.uuid4())[:8]}",
                category="Missing Evidence",
                description=f"No source evidence covers these query keywords: {', '.join(missing_keywords)}.",
                severity="High"
            ))
            ctx.add_trace(f"Anomaly detected: Missing evidence for keywords: {missing_keywords}")

        # 2. Check for duplicate knowledge (Jaccard similarity > 0.8)
        for i in range(len(evidence)):
            w1 = set(re.findall(r"\w+", evidence[i].fact.lower()))
            for j in range(i + 1, len(evidence)):
                w2 = set(re.findall(r"\w+", evidence[j].fact.lower()))
                
                intersection = len(w1 & w2)
                union = len(w1 | w2)
                jaccard = (intersection / union) if union > 0 else 0.0
                
                if jaccard > 0.8:
                    conflicts.append(Conflict(
                        conflict_id=f"cf-dup-{str(uuid.uuid4())[:8]}",
                        category="Duplicate Knowledge",
                        description=f"Redundant facts detected: '{evidence[i].fact[:40]}...' and '{evidence[j].fact[:40]}...'",
                        offending_sources=list(set([evidence[i].source, evidence[j].source])),
                        severity="Low"
                    ))

        # 3. Check for conflicting facts / contradictory sources
        # We look for opposite terms (e.g. "increases" vs "decreases", "implemented" vs "deprecated")
        positive_terms = {"increase", "improve", "accelerate", "faster", "positive", "higher", "scalable", "support", "implemented"}
        negative_terms = {"decrease", "degrade", "slow down", "slower", "negative", "lower", "bottleneck", "deprecated", "unsupported"}

        for i in range(len(evidence)):
            fact1 = evidence[i].fact.lower()
            w1 = set(re.findall(r"\w+", fact1))
            
            for j in range(i + 1, len(evidence)):
                fact2 = evidence[j].fact.lower()
                w2 = set(re.findall(r"\w+", fact2))
                
                # Check if they share significant terms (e.g. topic name) but clash on polarity
                shared = {w for w in (w1 & w2) if len(w) > 4 and w not in (
                    "system", "application", "benchmark", "using", "project", "approach", "results", "latency"
                )}
                
                if shared:
                    has_pos1 = any(w in fact1 for w in positive_terms)
                    has_neg1 = any(w in fact1 for w in negative_terms)
                    has_pos2 = any(w in fact2 for w in positive_terms)
                    has_neg2 = any(w in fact2 for w in negative_terms)
                    
                    if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
                        conflicts.append(Conflict(
                            conflict_id=f"cf-con-{str(uuid.uuid4())[:8]}",
                            category="Contradictory Sources",
                            description=f"Contradictory assertions detected on topic '{list(shared)[0]}': '{evidence[i].fact[:50]}' vs '{evidence[j].fact[:50]}'",
                            offending_sources=list(set([evidence[i].source, evidence[j].source])),
                            severity="High"
                        ))
                        ctx.add_trace(f"Contradiction flagged on topic '{list(shared)[0]}'")

        # 4. Check for low-confidence conclusions
        for ev in evidence:
            if ev.confidence < 0.5:
                conflicts.append(Conflict(
                    conflict_id=f"cf-conf-{str(uuid.uuid4())[:8]}",
                    category="Low Confidence",
                    description=f"Evidence fact '{ev.fact[:40]}...' has low confidence score of {ev.confidence}.",
                    offending_sources=[ev.source],
                    severity="Medium"
                ))

        ctx.add_trace(f"Anomaly check completed. Detected {len(conflicts)} discrepancies.")
        return conflicts
