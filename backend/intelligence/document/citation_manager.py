"""Tracks, matches, and constructs verified citation references from retrieved document segments."""

from typing import List, Dict, Any
from backend.intelligence.document.document_model import Citation


class CitationManager:
    """Constructs Citation schemas from search/retrieval results."""

    def create_citations(
        self,
        retrieved_chunks: List[Any],
        document_names: Dict[str, str],
        confidence_factor: float = 0.95
    ) -> List[Citation]:
        """Maps raw chunks to structured Citation references.

        Args:
            retrieved_chunks: Chunks matched by the query engine.
            document_names: Dict mapping document_id to filename.
            confidence_factor: Base confidence value.

        Returns:
            List[Citation]: Formatted citations.
        """
        citations = []
        for idx, chunk in enumerate(retrieved_chunks):
            # Extract content and chunk_id properties safely
            chunk_id = getattr(chunk, "chunk_id", f"chunk-{idx}")
            
            # Resolve document_id from chunk ID format (e.g. "doc-abc-1" -> "doc-abc")
            parts = chunk_id.split("-")
            if len(parts) >= 2 and parts[0] == "doc":
                doc_id = f"{parts[0]}-{parts[1]}"
            else:
                doc_id = parts[0] if parts else "unknown"

            doc_name = document_names.get(doc_id, "Unknown Document")
            
            text_content = getattr(chunk, "text", getattr(chunk, "content", ""))
            if not text_content:
                text_content = str(chunk)

            # Look up section fields from chunk objects
            section_name = getattr(chunk, "section", "General")
            if section_name == "General" and hasattr(chunk, "metadata"):
                meta = getattr(chunk, "metadata", {})
                if isinstance(meta, dict):
                    section_name = meta.get("section", "General")

            # Degrade confidence slightly for lower-ranked results
            chunk_conf = max(0.5, confidence_factor - (idx * 0.04))

            citations.append(Citation(
                document_id=doc_id,
                document_name=doc_name,
                section=section_name,
                text_chunk=text_content,
                chunk_id=chunk_id,
                confidence=round(chunk_conf, 2),
                evidence=text_content.strip()
            ))

        return citations
