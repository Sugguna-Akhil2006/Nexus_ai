"""Matches query strings against document text chunks with precise citation metadata."""

import re
from typing import List, Dict, Tuple, Any
from backend.intelligence.document.document_model import Citation
from backend.intelligence.document.chunk_manager import TextChunk


class CitationEngine:
    """Retrieves document segments matching queries and outputs source citations."""

    def search_and_cite(
        self,
        query: str,
        document_chunks: Dict[str, List[TextChunk]],  # Key is document_id
        document_names: Dict[str, str],             # Key is document_id
        limit: int = 3
    ) -> Tuple[str, List[Citation]]:
        """Finds matching source chunks and generates a mock response with citations.

        Args:
            query: Question or search phrase.
            document_chunks: Dict of document chunks.
            document_names: Dict mapping document_id to filename.
            limit: Maximum citation results.

        Returns:
            Tuple[str, List[Citation]]: (Generated Answer, Citations list)
        """
        if not query or not document_chunks:
            return "No matching content found to query.", []

        # Tokenize query to find keyword matches
        stop_words = {"the", "a", "an", "is", "are", "of", "in", "on", "at", "for", "to", "with", "and", "or"}
        query_words = [w.lower() for w in re.findall(r"\w+", query) if w.lower() not in stop_words]
        
        matches: List[Tuple[float, str, str, TextChunk]] = []  # (score, doc_id, doc_name, chunk)
        
        for doc_id, chunks in document_chunks.items():
            doc_name = document_names.get(doc_id, "Unknown Document")
            for chunk in chunks:
                score = 0.0
                chunk_text_lower = chunk.text.lower()
                
                # Check exact phrase match
                if query.lower() in chunk_text_lower:
                    score += 10.0
                
                # Keyword matching
                for qw in query_words:
                    if qw in chunk_text_lower:
                        score += 1.0
                
                if score > 0.0:
                    matches.append((score, doc_id, doc_name, chunk))

        # Sort matches by score descending
        matches.sort(key=lambda x: x[0], reverse=True)
        top_matches = matches[:limit]
        
        if not top_matches:
            # Fallback if no keyword matches at all: return first chunk of first doc
            first_doc_id = list(document_chunks.keys())[0]
            first_chunks = document_chunks[first_doc_id]
            if first_chunks:
                top_matches = [(0.1, first_doc_id, document_names.get(first_doc_id, "Unknown"), first_chunks[0])]

        citations = []
        answer_parts = []
        
        for idx, (score, doc_id, doc_name, chunk) in enumerate(top_matches, start=1):
            citations.append(Citation(
                document_id=doc_id,
                document_name=doc_name,
                section=chunk.section,
                text_chunk=chunk.text
            ))
            
            # Build answer based on citation snippets
            clean_snippet = chunk.text.strip().replace("\n", " ")
            if len(clean_snippet) > 150:
                clean_snippet = clean_snippet[:150] + "..."
            answer_parts.append(f"[{idx}] Source states: \"{clean_snippet}\" (from {doc_name}, section '{chunk.section}')")

        answer_intro = f"Based on the documents provided, here is the synthesized answer to your query: \"{query}\".\n\n"
        answer_body = "\n".join(answer_parts)
        answer = answer_intro + answer_body
        
        return answer, citations
