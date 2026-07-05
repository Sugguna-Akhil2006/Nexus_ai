"""Heuristic Jaccard overlap solvers for Duplicate and Near-Duplicate detection."""

import re
from typing import List, Dict, Set, Tuple
from backend.intelligence.document.document_model import SimilarityMapping


class DocumentSimilarityEngine:
    """Computes similarity coefficients and flags duplicate documents."""

    def is_duplicate(self, text1: str, text2: str) -> bool:
        """Returns True if document texts are identical (whitespace-stripped)."""
        return text1.strip() == text2.strip()

    def is_near_duplicate(self, text1: str, text2: str, threshold: float = 0.85) -> bool:
        """Determines if texts are near-duplicates using word-level Jaccard coefficient.

        Args:
            text1: Base text string.
            text2: Compare target text string.
            threshold: Minimum coefficient score (0.0 to 1.0) to flag duplicate.

        Returns:
            bool: True if Jaccard similarity exceeds threshold.
        """
        score = self.compute_text_jaccard(text1, text2)
        return score >= threshold

    def compute_text_jaccard(self, text1: str, text2: str) -> float:
        """Calculates token-level Jaccard coefficient between two texts."""
        stop_words = {"the", "a", "an", "is", "of", "and", "or", "in", "to", "for"}
        
        words1 = {w.lower() for w in re.findall(r'\w+', text1) if w.lower() not in stop_words}
        words2 = {w.lower() for w in re.findall(r'\w+', text2) if w.lower() not in stop_words}
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def compute_similarity_mappings(
        self,
        doc_texts: Dict[str, str],
        doc_names: Dict[str, str],
        doc_kws: Dict[str, List[str]]
    ) -> List[SimilarityMapping]:
        """Generates pairwise similarity metrics across a collection of documents."""
        mappings = []
        doc_ids = list(doc_texts.keys())
        
        for id1 in doc_ids:
            for id2 in doc_ids:
                if id1 == id2:
                    continue
                
                # Combine keyword Jaccard overlap and text Jaccard overlap
                kws1 = set(doc_kws.get(id1, []))
                kws2 = set(doc_kws.get(id2, []))
                
                union_kws = kws1.union(kws2)
                intersection_kws = kws1.intersection(kws2)
                kw_score = len(intersection_kws) / len(union_kws) if union_kws else 0.0
                
                text_score = self.compute_text_jaccard(doc_texts[id1], doc_texts[id2])
                
                # Average similarity score
                avg_score = (kw_score * 0.4) + (text_score * 0.6)
                
                mappings.append(SimilarityMapping(
                    target_document_id=id2,
                    target_document_name=doc_names.get(id2, "Unknown"),
                    similarity_score=round(avg_score, 2),
                    common_topics=list(intersection_kws)
                ))
                
        return mappings
