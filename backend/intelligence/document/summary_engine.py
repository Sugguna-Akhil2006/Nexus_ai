"""Generates diverse summarization types (executive, technical, bullet, section-by-section, custom)."""

import re
from typing import List, Dict, Any, Optional
from backend.intelligence.document.document_model import SummaryDetail
from backend.intelligence.document.chunk_manager import TextChunk


class SummaryEngine:
    """Compiles document text streams into multi-dimensional summaries."""

    def summarize(
        self,
        chunks: List[TextChunk],
        custom_prompt: Optional[str] = None
    ) -> SummaryDetail:
        """Processes chunks to compile summaries.

        Args:
            chunks: List of document chunks.
            custom_prompt: Custom prompt instruction.

        Returns:
            SummaryDetail: Populated summary formats.
        """
        if not chunks:
            return SummaryDetail(
                executive="No content to summarize.",
                technical="No content to summarize.",
                bullet=[],
                section_by_section={}
            )

        # Merge text
        full_text = "\n\n".join(chunk.text for chunk in chunks)
        
        # 1. Executive Summary
        # Extract the first paragraph or first 3 sentences for executive overview
        sentences = re.split(r'(?<=[.!?])\s+', full_text.strip())
        executive_sentences = sentences[:3]
        executive = " ".join(executive_sentences)
        if not executive:
            executive = "High-level overview of the uploaded document contents."
        else:
            executive = "Executive Summary: " + executive

        # 2. Technical Summary
        # Focus on technical vocabulary, numbers, formats, metrics, or files
        tech_words = {"class", "function", "def", "import", "package", "docker", "python", "java", "schema", "api", "database", "git", "config"}
        numbers = re.findall(r'\b\d+\b', full_text)
        found_techs = []
        for word in re.findall(r'\b\w+\b', full_text.lower()):
            if word in tech_words and word not in found_techs:
                found_techs.append(word)
                
        technical = f"Technical metadata highlights: Found {len(sentences)} text sentences, {len(numbers)} numerical parameters, "
        if found_techs:
            technical += f"and technical tags: {', '.join(found_techs)}."
        else:
            technical += "with standard text formatting."

        # 3. Bullet Summary
        # Take key sentences or paragraph summaries as bullet points
        bullets = []
        for i in range(0, len(sentences), max(1, len(sentences) // 4)):
            sent = sentences[i].strip()
            if sent and len(sent) > 20 and len(bullets) < 5:
                # Clean clean line formatting
                bullets.append(sent)
        if not bullets:
            bullets = ["No distinct bullet summaries extracted."]

        # 4. Section-by-section Summary
        # Group by chunks section header
        sections_map = {}
        for chunk in chunks:
            sect = chunk.section or "General"
            if sect not in sections_map:
                sections_map[sect] = []
            sections_map[sect].append(chunk.text)
            
        section_by_section = {}
        for sect, texts in sections_map.items():
            sect_text = " ".join(texts)[:200]
            sect_sentences = re.split(r'(?<=[.!?])\s+', sect_text.strip())
            summary_sentence = sect_sentences[0] if sect_sentences else "Section details."
            section_by_section[sect] = summary_sentence

        # 5. Custom prompt-based summary
        custom = None
        if custom_prompt:
            custom = f"Custom Summary (Prompt: '{custom_prompt}'): Synthesized document response analyzing "
            custom += ", ".join(sentences[1:3]) if len(sentences) > 2 else "content."

        return SummaryDetail(
            executive=executive,
            technical=technical,
            bullet=bullets,
            section_by_section=section_by_section,
            custom=custom
        )
