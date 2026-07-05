"""Compiles searchable inverted indices for Concept, Entity, Topic, and Citation fields."""

import re
from typing import List, Dict, Set
from backend.intelligence.document.models import SemanticIndex, EntityNode
from backend.intelligence.document.chunk_manager import TextChunk
from backend.intelligence.document.document_model import Topic


class SemanticIndexBuilder:
    """Builds reusable indices mapping query keys to matching text chunks."""

    def build_index(
        self,
        chunks: List[TextChunk],
        entities: List[EntityNode],
        topics: List[Topic]
    ) -> SemanticIndex:
        """Assembles distinct inverted index mappings.

        Args:
            chunks: Segmented document chunks.
            entities: Extracted entity nodes.
            topics: Classified domain topics.

        Returns:
            SemanticIndex: Populated index model.
        """
        concept_index: Dict[str, List[str]] = {}
        entity_index: Dict[str, List[str]] = {}
        topic_index: Dict[str, List[str]] = {}
        citation_index: Dict[str, List[str]] = {}

        stop_words = {
            "the", "a", "an", "is", "are", "of", "in", "on", "at", "for", "to", "with",
            "and", "or", "but", "this", "that", "it", "be", "was", "were", "been", "have", "has"
        }

        for chunk in chunks:
            text_lower = chunk.text.lower()
            
            # 1. Concept indexing: tokenize chunk text
            words = set(re.findall(r'\b\w+\b', text_lower))
            for w in words:
                if w not in stop_words and len(w) > 3:
                    if w not in concept_index:
                        concept_index[w] = []
                    # Keep text snippet
                    if chunk.text not in concept_index[w]:
                        concept_index[w].append(chunk.text)

            # 2. Entity indexing: match pre-extracted entities in this chunk
            for ent in entities:
                ent_lbl = ent.name.lower()
                if ent_lbl in text_lower:
                    ent_name = ent.name
                    if ent_name not in entity_index:
                        entity_index[ent_name] = []
                    if chunk.text not in entity_index[ent_name]:
                        entity_index[ent_name].append(chunk.text)

            # 3. Topic indexing: match topics
            for top in topics:
                top_lbl = top.name.lower()
                # Check if topic keyword exists in chunk
                if top_lbl in text_lower or (chunk.section and top_lbl in chunk.section.lower()):
                    top_name = top.name
                    if top_name not in topic_index:
                        topic_index[top_name] = []
                    if chunk.text not in topic_index[top_name]:
                        topic_index[top_name].append(chunk.text)

            # 4. Citation indexing: map section/headers
            sect_key = chunk.section or "General"
            if sect_key not in citation_index:
                citation_index[sect_key] = []
            if chunk.text not in citation_index[sect_key]:
                citation_index[sect_key].append(chunk.text)

        return SemanticIndex(
            concept_index=concept_index,
            entity_index=entity_index,
            topic_index=topic_index,
            citation_index=citation_index
        )

    def search_index(self, index: SemanticIndex, search_type: str, query: str) -> List[str]:
        """Searches the specified index for matches.

        Args:
            index: SemanticIndex model.
            search_type: 'concept', 'entity', 'topic', or 'citation'.
            query: Target query text.

        Returns:
            List[str]: Matching text chunks snippets.
        """
        st = search_type.lower().strip()
        q = query.lower().strip()
        
        if st == "concept":
            # Match keywords
            return index.concept_index.get(q, [])
        elif st == "entity":
            # Check key matching
            for key in index.entity_index:
                if key.lower() == q:
                    return index.entity_index[key]
            return []
        elif st == "topic":
            # Check topic matching
            for key in index.topic_index:
                if key.lower() == q:
                    return index.topic_index[key]
            return []
        elif st == "citation":
            # Check citation key
            for key in index.citation_index:
                if key.lower() == q or q in key.lower():
                    return index.citation_index[key]
            return []
            
        return []
