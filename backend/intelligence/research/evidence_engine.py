"""Extracts research claims, hypotheses, evidence sections, and confidence scores."""

import re
from typing import Dict, List, Any
from backend.intelligence.research.models import ResearchPaperMetadata


class EvidenceEngine:
    """Scans research paper content to build an Evidence Matrix of claims and findings."""

    def extract_evidence(
        self,
        paper: ResearchPaperMetadata,
        raw_text: str
    ) -> List[Dict[str, Any]]:
        """Identifies key claims, hypotheses, and supporting statistics in the text.

        Returns:
            List[Dict[str, Any]]: List of evidence items containing:
                - claim: The extracted claim or finding sentence.
                - type: "Claim", "Hypothesis", or "Statistic".
                - context: Context paragraph surrounding the claim.
                - confidence: Score reflecting support strength.
                - paper_id: ID of the originating source paper.
                - title: Title of the source paper.
        """
        evidence_items = []
        paragraphs = [p.strip() for p in raw_text.split("\n\n") if len(p.strip()) > 30]

        claim_patterns = [
            (re.compile(r"\b(showed|demonstrates|conclude|demonstrated|finds|proves?|indicates)\b", re.IGNORECASE), "Claim"),
            (re.compile(r"\b(hypothesize|suggests|propose|proposes|speculate)\b", re.IGNORECASE), "Hypothesis"),
            (re.compile(r"\b(\d+%\s*increase|\bstatistically significant\b|p\s*<\s*0\.\d+|accuracy\b)\b", re.IGNORECASE), "Statistic")
        ]

        for p_idx, para in enumerate(paragraphs):
            # Split paragraph into sentences
            sentences = re.split(r"(?<=[.!?])\s+", para)
            for sentence in sentences:
                matched_type = None
                
                # Check patterns
                for regex, type_name in claim_patterns:
                    if regex.search(sentence):
                        matched_type = type_name
                        break
                
                if matched_type:
                    # Assign confidence score heuristically
                    confidence = 0.70
                    if matched_type == "Statistic":
                        confidence = 0.90
                    elif matched_type == "Claim":
                        confidence = 0.80
                        # Boost if has numbers
                        if any(char.isdigit() for char in sentence):
                            confidence = 0.85

                    # Limit the context size
                    context = para[:250] + "..." if len(para) > 250 else para
                    
                    evidence_items.append({
                        "claim": sentence.strip(),
                        "type": matched_type,
                        "context": context,
                        "confidence": confidence,
                        "paper_id": paper.paper_id,
                        "title": paper.title
                    })

                    # Limit to max 5 key claims per paper to avoid massive output
                    if len(evidence_items) >= 5:
                        return evidence_items

        return evidence_items
