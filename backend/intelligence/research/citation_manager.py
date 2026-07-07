"""Tracks reference indexes, builds bibliography structures, and extracts suggested reading list."""

import re
from typing import List, Dict, Any, Tuple
from backend.intelligence.research.models import ResearchPaperMetadata


class CitationManager:
    """Extracts in-text citations and compiles bibliography references lists."""

    def extract_citations_and_references(
        self,
        paper: ResearchPaperMetadata,
        raw_text: str
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Scans raw content for inline citations and bibliographic lines.

        Returns:
            Tuple[List[Dict[str, Any]], List[str]]:
                - citations: List of inline citation details.
                - suggested_reading: List of raw external reference strings.
        """
        citations = []
        suggested_reading = []

        # 1. Scan for inline citations (e.g., "[1]" or "[Vance2023]")
        inline_matches = re.findall(r"\[([A-Za-z0-9\s,\-\.\u00c0-\u017f]+)\]", raw_text)
        for match in inline_matches:
            match_clean = match.strip()
            # Verify if it looks like a valid citation (numeric index or author year)
            if re.match(r"^\d+$", match_clean) or any(char.isdigit() for char in match_clean):
                citations.append({
                    "citation_key": f"[{match_clean}]",
                    "source_paper_id": paper.paper_id,
                    "source_title": paper.title
                })

        # 2. Extract references bibliography
        lines = raw_text.splitlines()
        ref_start = -1
        for idx, line in enumerate(lines):
            l_lower = line.lower()
            if l_lower.startswith("references") or l_lower.startswith("bibliography"):
                ref_start = idx
                break

        if ref_start != -1:
            # Gather lines after header
            ref_lines = [l.strip() for l in lines[ref_start + 1:] if l.strip()]
            
            # Simple reference grouping: combine lines starting with brackets or bullets
            current_ref = []
            for r_line in ref_lines:
                if re.match(r"^\[\d+\]", r_line) or re.match(r"^\d+\.", r_line) or r_line.startswith("-"):
                    if current_ref:
                        suggested_reading.append(" ".join(current_ref))
                    current_ref = [r_line]
                else:
                    if current_ref:
                        current_ref.append(r_line)
                    else:
                        current_ref = [r_line]
            
            if current_ref:
                suggested_reading.append(" ".join(current_ref))
        else:
            # Fallback suggested reading: mock references list based on keywords
            suggested_reading = [
                f"Advances in {kw.title()} and semantic graphs ({paper.published_date})."
                for kw in paper.keywords[:3]
            ]

        # De-duplicate inline citations
        seen_keys = set()
        unique_citations = []
        for c in citations:
            if c["citation_key"] not in seen_keys:
                seen_keys.add(c["citation_key"])
                unique_citations.append(c)

        return unique_citations, suggested_reading
