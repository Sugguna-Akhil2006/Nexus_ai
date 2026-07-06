"""Extracts structured metadata details from research paper texts."""

import re
from typing import List, Optional
from backend.intelligence.research.models import ResearchPaperMetadata


class PaperParser:
    """Parses raw text segments of research papers to isolate structured metadata."""

    def parse_paper_text(self, paper_id: str, text: str) -> ResearchPaperMetadata:
        """Heuristically extracts key metadata fields from a paper's text content."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        # 1. Title Extraction
        title = "Untitled Research Paper"
        if lines:
            # Pick first non-empty header-like line
            for line in lines[:3]:
                if len(line) > 10 and not line.lower().startswith("abstract"):
                    title = line
                    break

        # 2. Abstract Extraction
        abstract = ""
        # Search for Abstract keyword
        abstract_start = -1
        intro_start = -1
        
        for idx, line in enumerate(lines):
            l_lower = line.lower()
            if abstract_start == -1 and (l_lower.startswith("abstract") or "abstract" in l_lower[:12]):
                abstract_start = idx
            elif intro_start == -1 and (l_lower.startswith("1. intro") or l_lower.startswith("introduction") or l_lower.startswith("1 introduction")):
                intro_start = idx

        if abstract_start != -1:
            end_idx = intro_start if intro_start > abstract_start else (abstract_start + 5)
            abstract_lines = lines[abstract_start:end_idx]
            abstract = " ".join(abstract_lines)
            # Remove "Abstract" prefix
            abstract = re.sub(r"(?i)^abstract:?\s*", "", abstract).strip()
        else:
            # Fallback abstract: take the first 4 lines after title
            abstract = " ".join(lines[1:5]) if len(lines) > 5 else "No abstract content could be determined."

        # 3. Authors Extraction
        authors = []
        for line in lines[1:4]:
            if any(char.isdigit() for char in line) or "@" in line or "abstract" in line.lower() or line == title:
                continue
            # Split names by comma or and
            names = re.split(r",|\band\b", line)
            for name in names:
                name_clean = name.strip()
                if len(name_clean) > 3 and len(name_clean.split()) <= 4:
                    authors.append(name_clean)
        if not authors:
            authors = ["Unknown Author"]

        # 4. Keywords
        keywords = []
        for line in lines:
            if line.lower().startswith("keywords:") or line.lower().startswith("key words:"):
                kw_str = re.sub(r"(?i)^key\s*words:?\s*", "", line)
                keywords = [k.strip() for k in re.split(r",|;", kw_str) if k.strip()]
                break
        if not keywords:
            # Extract high frequency words from title/abstract
            words = re.findall(r"\b\w{4,12}\b", abstract.lower())
            freq = {}
            for w in words:
                if w not in ("this", "that", "with", "from", "their", "paper", "research", "system", "study"):
                    freq[w] = freq.get(w, 0) + 1
            sorted_words = sorted(freq.keys(), key=lambda x: freq[x], reverse=True)
            keywords = sorted_words[:5]

        # 5. Venue and Year
        venue = "Academic Repository"
        published_date = "2026"
        text_sample = text[:1500]
        
        # Heuristically scan for years
        years = re.findall(r"\b(19\d{2}|20[0-2]\d)\b", text_sample)
        if years:
            published_date = years[0]

        # Scanning for common venues
        for kw, full_venue in [
            ("arxiv", "arXiv Pre-print Archive"),
            ("ieee", "IEEE Conference Proceedings"),
            ("acm", "ACM Digital Library"),
            ("springer", "Springer Link Journal"),
            ("nature", "Nature Publishing Group")
        ]:
            if kw in text_sample.lower():
                venue = full_venue
                break

        return ResearchPaperMetadata(
            paper_id=paper_id,
            title=title,
            authors=authors,
            abstract=abstract,
            published_date=published_date,
            venue=venue,
            keywords=keywords
        )
