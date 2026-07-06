"""Compares claims, keywords, and finding patterns across multiple research sources."""

import re
from typing import List, Dict, Any, Set
from backend.intelligence.research.models import ResearchPaperMetadata


class ComparisonEngine:
    """Evaluates consensus, contradictions, and common methodology stacks between papers."""

    def compare_papers(
        self,
        papers: List[ResearchPaperMetadata],
        evidence_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Performs analytical comparisons over ingested research data.

        Returns:
            Dict[str, Any]: Comparison metrics including consensus, differences, and overlaps.
        """
        if not papers:
            return {}

        # 1. Identify keyword overlaps (consensus topics)
        all_kw_sets = [set(p.keywords) for p in papers]
        consensus_kws = set.intersection(*all_kw_sets) if all_kw_sets else set()
        
        # All unique keywords
        union_kws = set.union(*all_kw_sets) if all_kw_sets else set()
        unique_to_paper = {}
        for p in papers:
            p_kws = set(p.keywords)
            others_kws = set()
            for other in papers:
                if other.paper_id != p.paper_id:
                    others_kws.update(other.keywords)
            unique_to_paper[p.title] = sorted(list(p_kws - others_kws))

        # 2. Heuristically detect potential contradictions
        contradictions = []
        positive_terms = {"increase", "improve", "accelerate", "faster", "positive", "higher", "scalable"}
        negative_terms = {"decrease", "degrade", "slow down", "slower", "negative", "lower", "bottleneck"}

        # Compare pairs of evidence claims
        for i in range(len(evidence_list)):
            for j in range(i + 1, len(evidence_list)):
                e1 = evidence_list[i]
                e2 = evidence_list[j]
                
                # Only check if from different papers
                if e1["paper_id"] == e2["paper_id"]:
                    continue
                
                # Check if they mention same technology or keyword
                shared_words = set(re.findall(r"\w+", e1["claim"].lower())) & set(re.findall(r"\w+", e2["claim"].lower()))
                # Ignore common stopwords
                relevant_shared = {w for w in shared_words if len(w) > 4 and w not in (
                    "this", "with", "system", "using", "project", "approach", "results", "model", "analysis"
                )}
                
                if relevant_shared:
                    # Check for polarity clash
                    c1_lower = e1["claim"].lower()
                    c2_lower = e2["claim"].lower()
                    
                    has_pos1 = any(w in c1_lower for w in positive_terms)
                    has_neg1 = any(w in c1_lower for w in negative_terms)
                    has_pos2 = any(w in c2_lower for w in positive_terms)
                    has_neg2 = any(w in c2_lower for w in negative_terms)
                    
                    if (has_pos1 and has_neg2) or (has_neg1 and has_pos2):
                        contradictions.append({
                            "keyword": list(relevant_shared)[0],
                            "paper1_title": e1["title"],
                            "paper1_claim": e1["claim"],
                            "paper2_title": e2["title"],
                            "paper2_claim": e2["claim"]
                        })

        return {
            "consensus_keywords": sorted(list(consensus_kws)),
            "all_unique_keywords": sorted(list(union_kws)),
            "unique_keywords_by_source": unique_to_paper,
            "detected_contradictions": contradictions
        }
