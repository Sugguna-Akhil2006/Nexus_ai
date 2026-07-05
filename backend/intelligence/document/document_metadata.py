"""Extracts document metadata, titles, format, word/line metrics, and keywords."""

import os
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.intelligence.document.document_model import DocumentMetadata


class MetadataExtractor:
    """Extracts structural and semantic metadata from raw document text/bytes."""

    def extract_metadata(
        self,
        content: str,
        filename: str,
        custom_meta: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """Parses raw text to extract metadata attributes.

        Args:
            content: Raw string content.
            filename: Original filename.
            custom_meta: Optional override meta fields.

        Returns:
            DocumentMetadata: Extracted attributes.
        """
        custom = custom_meta or {}
        
        # 1. Format
        _, ext = os.path.splitext(filename.lower())
        fmt = ext.upper().lstrip(".").strip()
        if not fmt:
            fmt = "TXT"

        # 2. Word & Line counts
        words = re.findall(r'\b\w+\b', content)
        word_count = len(words)
        line_count = len(content.splitlines())

        # 3. Title extraction
        title = ""
        # HTML Title
        html_title = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        if html_title:
            title = html_title.group(1).strip()
        # Markdown Heading
        if not title:
            md_title = re.search(r'^#\s+(.*?)$', content, re.MULTILINE)
            if md_title:
                title = md_title.group(1).strip()
        # JSON Title
        if not title and fmt == "JSON":
            try:
                import json
                data = json.loads(content)
                if isinstance(data, dict):
                    title = data.get("title") or data.get("name") or ""
            except Exception:
                pass
        # Fallback to first line
        if not title:
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            if lines:
                first_line = lines[0]
                if len(first_line) < 100:
                    title = first_line
        # Final fallback to filename
        if not title:
            title = os.path.splitext(filename)[0].replace("_", " ").title()

        # 4. Author extraction
        author = custom.get("author")
        if not author:
            # Look for Author: Name
            author_match = re.search(r'(?:author|by):\s*(.*?)$', content, re.IGNORECASE | re.MULTILINE)
            if author_match:
                author = author_match.group(1).strip()
            else:
                author = "Nexus System Ingestion"

        # 5. Creation Date
        creation_date = custom.get("creation_date") or datetime.utcnow().isoformat()

        # 6. Keyword extraction (top 5 frequent non-stopwords)
        stop_words = {
            "the", "a", "an", "is", "are", "of", "in", "on", "at", "for", "to", "with",
            "and", "or", "but", "this", "that", "it", "he", "she", "they", "we", "i",
            "you", "be", "was", "were", "been", "have", "has", "had", "do", "does", "did"
        }
        word_freq = {}
        for w in words:
            wl = w.lower()
            if wl not in stop_words and len(wl) > 3:
                word_freq[wl] = word_freq.get(wl, 0) + 1
        
        sorted_kws = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [kw for kw, freq in sorted_kws[:5]]

        return DocumentMetadata(
            title=title,
            author=author,
            creation_date=creation_date,
            format=fmt,
            word_count=word_count,
            line_count=line_count,
            keywords=keywords,
            custom_metadata=custom
        )
