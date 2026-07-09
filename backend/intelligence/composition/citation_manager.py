"""Citation manager — indexes, ranks, and formats citations for composed output."""

from __future__ import annotations

from typing import Dict, List, Optional

from backend.intelligence.contracts.response_models import Citation


class CitationManager:
    """Manages a pool of citations collected from multiple module responses.

    Provides indexed access, relevance ranking, source-type filtering,
    and markdown-formatted reference rendering.
    """

    def __init__(self) -> None:
        self._citations: Dict[str, Citation] = {}   # citation_id → Citation

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def add(self, citation: Citation) -> None:
        """Adds or replaces a citation by ``citation_id``."""
        self._citations[citation.citation_id] = citation

    def add_many(self, citations: List[Citation]) -> None:
        """Bulk-adds citations."""
        for cit in citations:
            self.add(cit)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, citation_id: str) -> Optional[Citation]:
        """Returns a citation by its ID, or None if not found."""
        return self._citations.get(citation_id)

    def all_citations(self) -> List[Citation]:
        """Returns all managed citations sorted by relevance descending."""
        return sorted(
            self._citations.values(),
            key=lambda c: c.relevance_score,
            reverse=True,
        )

    def filter_by_source_type(self, source_type: str) -> List[Citation]:
        """Returns citations of a specific source type.

        Args:
            source_type: e.g. "document", "url", "knowledge_base", "memory".

        Returns:
            Filtered and relevance-ranked citations.
        """
        return sorted(
            [c for c in self._citations.values() if c.source_type == source_type],
            key=lambda c: c.relevance_score,
            reverse=True,
        )

    def top_n(self, n: int) -> List[Citation]:
        """Returns the top *n* citations by relevance score."""
        return self.all_citations()[:n]

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def to_markdown(self) -> str:
        """Renders all citations as a numbered markdown reference list.

        Returns:
            Multi-line markdown string.
        """
        lines: List[str] = ["## References\n"]
        for i, cit in enumerate(self.all_citations(), start=1):
            title = cit.title or cit.identifier
            snippet = f" — *{cit.snippet[:80]}…*" if cit.snippet else ""
            lines.append(
                f"{i}. **[{title}]** "
                f"(`{cit.source_type}` | relevance: {cit.relevance_score:.2f})"
                f"{snippet}"
            )
        return "\n".join(lines)

    def __len__(self) -> int:
        return len(self._citations)
