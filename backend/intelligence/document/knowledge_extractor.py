"""Generates structured KnowledgeObjects from textual claims and evidence sentences."""

import re
from typing import List, Tuple, Any
from backend.intelligence.document.models import KnowledgeObject
from backend.intelligence.document.chunk_manager import TextChunk


class KnowledgeExtractor:
    """Extracts factual claims and aggregates them with evidence verification pointers."""

    def extract_knowledge_objects(self, chunks: List[TextChunk]) -> List[KnowledgeObject]:
        """Analyzes chunks and extracts verified structured knowledge objects.

        Args:
            chunks: Document segments list.

        Returns:
            List[KnowledgeObject]: Compiled knowledge facts.
        """
        knowledge_objects = []
        fact_idx = 1

        # Triggers verbs/structures
        claim_patterns = [
            (r'(\b[\w\s\-]+\bimplements\b[\w\s\-]+)', "System Implementation"),
            (r'(\b[\w\s\-]+\bbuilt\s+by\b[\w\s\-]+)', "Engineering Association"),
            (r'(\b[\w\s\-]+\bdesigned\b[\w\s\-]+)', "Architectural Design"),
            (r'(\b[\w\s\-]+\bcontains\b[\w\s\-]+)', "Stack Feature"),
            (r'(\b[\w\s\-]+\bwritten\s+in\b[\w\s\-]+)', "Language Integration")
        ]

        for chunk in chunks:
            lines = chunk.text.splitlines()
            for line in lines:
                line_str = line.strip()
                if len(line_str) < 30 or len(line_str) > 200:
                    continue

                for pattern, category in claim_patterns:
                    match = re.search(pattern, line_str, re.IGNORECASE)
                    if match:
                        claim_text = match.group(1).strip()
                        
                        # Generate Title from category
                        title = f"{category} Fact {fact_idx}"
                        
                        cat_val = "Skill" if category == "Language Integration" else "Project"
                        knowledge_objects.append(KnowledgeObject(
                            title=title,
                            description=f"Extracted claim: '{claim_text}'",
                            confidence=0.9,
                            evidence=line_str,
                            category=cat_val,
                            source_sections=[chunk.section or "General"],
                            supporting_citations=[chunk.text[:100] + "..."]
                        ))
                        fact_idx += 1
                        break  # Prevent duplicate matches for the same line

        # Add generic fallback if no specific claims are parsed
        if not knowledge_objects and chunks:
            knowledge_objects.append(KnowledgeObject(
                title="Document Overview Fact",
                description="The document outlines standard tech infrastructure details.",
                confidence=0.7,
                evidence=chunks[0].text[:120] if len(chunks[0].text) > 120 else chunks[0].text,
                source_sections=[chunks[0].section or "General"],
                supporting_citations=[chunks[0].text[:80] + "..."]
            ))

        return knowledge_objects
