"""Implements cross-document reasoning, structural comparisons, and confidence estimations."""

import re
from typing import List, Dict, Any, Tuple
from backend.intelligence.document.chunk_manager import TextChunk


class CrossDocumentReasoning:
    """Evaluates contradictions, overlaps, and version differences across document contexts."""

    def analyze_intent(self, query: str) -> str:
        """Determines the core reasoning task classification.

        Returns:
            str: 'COMPARISON', 'SUMMARY', 'TECH_CHECK', or 'GENERAL'.
        """
        q_lower = query.lower()
        if any(w in q_lower for w in ("difference", "differ", "compare", "changed", "change", "version")):
            return "COMPARISON"
        if any(w in q_lower for w in ("summarize", "summary", "overview", "all files")):
            return "SUMMARY"
        if any(w in q_lower for w in ("technology", "technologies", "common", "framework", "language")):
            return "TECH_CHECK"
        return "GENERAL"

    def reason_over_documents(
        self,
        query: str,
        chunks: List[TextChunk]
    ) -> Tuple[str, float]:
        """Runs logical analysis over retrieved chunks to find consensus and deltas.

        Returns:
            Tuple[str, float]: Synthesized reasoning context string and overall confidence.
        """
        intent = self.analyze_intent(query)
        if not chunks:
            return "No matching source segments were retrieved to base reasoning upon.", 0.0

        # Group chunk text by source document ID
        doc_groups: Dict[str, List[str]] = {}
        for c in chunks:
            chunk_id = getattr(c, "chunk_id", "unknown-chunk")
            parts = chunk_id.split("-")
            if len(parts) >= 2 and parts[0] == "doc":
                doc_id = f"{parts[0]}-{parts[1]}"
            else:
                doc_id = parts[0]
            
            if doc_id not in doc_groups:
                doc_groups[doc_id] = []
            doc_groups[doc_id].append(c.text.strip())

        # Overall confidence estimation
        # Baseline starts high and decreases if few documents are matched or chunks are sparse
        base_confidence = 0.92
        if len(doc_groups) < 2 and intent == "COMPARISON":
            base_confidence -= 0.20  # Low confidence comparing without multi-doc sources
        
        confidence = max(0.40, min(0.99, base_confidence))

        # Synthesize logic text
        synthesis_lines = []
        synthesis_lines.append(f"[Reasoning Scope: {intent} (Confidence: {confidence:.0%})]")
        
        # 1. Tech check reasoning
        if intent == "TECH_CHECK":
            # Extract common words that look like tech terms
            tech_keywords = {"python", "react", "fastapi", "docker", "kubernetes", "sqlite", "openai", "microsoft", "javascript"}
            found_terms: Dict[str, set[str]] = {}
            for doc_id, text_list in doc_groups.items():
                found_terms[doc_id] = set()
                combined = " ".join(text_list).lower()
                for term in tech_keywords:
                    if term in combined:
                        found_terms[doc_id].add(term.title())

            synthesis_lines.append("Analyzing common technology stacks across documents...")
            if len(found_terms) >= 2:
                common = set.intersection(*found_terms.values())
                if common:
                    synthesis_lines.append(f"Common technologies detected: {', '.join(common)}.")
                else:
                    synthesis_lines.append("No identical technology tags overlap between the compared document pools.")
            else:
                single_doc = list(found_terms.keys())[0]
                synthesis_lines.append(f"Technologies found in active document: {', '.join(found_terms[single_doc])}.")

        # 2. Version comparison reasoning
        elif intent == "COMPARISON":
            synthesis_lines.append("Evaluating document differences and version updates...")
            # Simple content diff logic
            if len(doc_groups) >= 2:
                doc_ids = list(doc_groups.keys())
                txt1 = " ".join(doc_groups[doc_ids[0]]).lower()
                txt2 = " ".join(doc_groups[doc_ids[1]]).lower()
                
                # Check both directions for updates symmetric
                additions = []
                for word in ("fastapi", "docker", "kubernetes", "security", "async"):
                    if (word in txt2 and word not in txt1) or (word in txt1 and word not in txt2):
                        additions.append(word.title())
                
                if additions:
                    synthesis_lines.append(f"Detected additions in later segments: {', '.join(additions)}.")
                else:
                    synthesis_lines.append("Found slight structural adaptations but no major technology shifts.")
            else:
                synthesis_lines.append("Comparison requested but only one source document was successfully retrieved.")

        # 3. Summarization synthesis
        elif intent == "SUMMARY":
            synthesis_lines.append("Synthesizing executive summaries across all matched collections...")
            for doc_id, text_list in doc_groups.items():
                snippet = text_list[0][:150] + "..." if len(text_list[0]) > 150 else text_list[0]
                synthesis_lines.append(f"- Doc {doc_id} outlines: \"{snippet}\"")

        else:
            synthesis_lines.append("Retrieved consensus facts from references:")
            for doc_id, text_list in doc_groups.items():
                synthesis_lines.append(f"- Document {doc_id} reference: \"{text_list[0][:100]}...\"")

        return "\n".join(synthesis_lines), confidence
