"""Evidence merger — deduplicates and aggregates evidence across module responses."""

from __future__ import annotations

from typing import Dict, List, Set

from backend.intelligence.contracts.response_models import Citation, IntelligenceResponse


class EvidenceMerger:
    """Merges evidence from multiple ``IntelligenceResponse`` objects.

    Deduplication strategy:
    - Citations with the same ``identifier`` are considered duplicates.
    - The copy with the highest ``relevance_score`` wins.
    - Sources from multiple modules are listed in ``source_modules``.
    """

    @staticmethod
    def merge_citations(responses: List[IntelligenceResponse]) -> List[Citation]:
        """Merges citations from all responses, removing exact-identifier duplicates.

        Args:
            responses: List of module ``IntelligenceResponse`` objects.

        Returns:
            Deduplicated list of ``Citation`` objects ranked by relevance.
        """
        best: Dict[str, Citation] = {}  # identifier → best citation

        for resp in responses:
            for cit in resp.citations:
                existing = best.get(cit.identifier)
                if existing is None or cit.relevance_score > existing.relevance_score:
                    best[cit.identifier] = cit

        # Sort descending by relevance
        return sorted(best.values(), key=lambda c: c.relevance_score, reverse=True)

    @staticmethod
    def find_shared_evidence(
        responses: List[IntelligenceResponse],
    ) -> List[str]:
        """Returns citation identifiers referenced by more than one module.

        Args:
            responses: List of module responses.

        Returns:
            List of identifiers that appear across at least two modules.
        """
        seen: Dict[str, int] = {}
        for resp in responses:
            for cit in resp.citations:
                seen[cit.identifier] = seen.get(cit.identifier, 0) + 1
        return [ident for ident, count in seen.items() if count >= 2]

    @staticmethod
    def remove_duplicate_snippets(citations: List[Citation]) -> List[Citation]:
        """Removes citations whose ``snippet`` text is identical to an earlier entry.

        Args:
            citations: Pre-merged citation list.

        Returns:
            List with duplicate-snippet citations removed.
        """
        seen_snippets: Set[str] = set()
        unique: List[Citation] = []
        for cit in citations:
            key = cit.snippet.strip().lower() if cit.snippet else cit.identifier
            if key not in seen_snippets:
                seen_snippets.add(key)
                unique.append(cit)
        return unique
