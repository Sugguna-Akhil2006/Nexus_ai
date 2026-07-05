"""Extracts structured entity nodes (People, Technologies, Organizations, locations, Standards, etc.)."""

import re
from typing import List, Set, Dict, Any
from backend.intelligence.document.models import EntityNode


class EntityExtractor:
    """Extracts named entities from raw document text using lookup mapping heuristics."""

    def __init__(self) -> None:
        # Define vocabulary maps for structured entities
        self.vocab = {
            "Programming Languages": {"python", "go", "java", "typescript", "javascript", "c++", "c#", "rust", "ruby", "php"},
            "Frameworks": {"fastapi", "react", "node.js", "django", "vue.js", "flask", "angular", "next.js", "spring", "pytorch"},
            "Technologies": {"docker", "kubernetes", "git", "sql", "sqlite", "postgresql", "qdrant", "mongodb", "redis", "nginx", "rest api", "grpc", "aws", "gcp", "azure"},
            "Organizations": {"openai", "deepmind", "microsoft", "nexus ai", "google", "meta", "amazon", "apple", "ibm", "oracle"},
            "Locations": {"london", "new york", "san francisco", "california", "seattle", "boston", "chicago", "tokyo", "paris"},
            "Standards": {"rest", "json", "csv", "xml", "html", "pdf", "docx", "utf-8", "iso 8601", "oauth2", "jwt"},
            "Products": {"nexus engine", "resume intelligence", "github intelligence", "document intelligence", "meeting intelligence"},
            "People": {"alice", "bob", "charlie", "john doe", "jane smith", "sugguna-akhil2006", "akhil"},
            "Projects": {"project alpha", "project beta", "nexus project", "enterprise knowledge base"}
        }

    def extract_entities(self, text: str) -> List[EntityNode]:
        """Analyzes text block and returns identified entity nodes.

        Args:
            text: Raw input string.

        Returns:
            List[EntityNode]: Extracted entity nodes.
        """
        entities = []
        found = set()
        text_lower = text.lower()

        # 1. Vocabulary mapping matches
        for category, terms in self.vocab.items():
            for term in terms:
                # Use word boundaries or sub-phrases matches
                pattern = r'\b' + re.escape(term) + r'\b'
                if term == "rest api":
                    pattern = r'\brest\s+api\b'
                elif term == "nexus ai":
                    pattern = r'\bnexus\s+ai\b'
                elif term == "nexus project":
                    pattern = r'\bnexus\s+project\b'
                elif term == "project alpha":
                    pattern = r'\bproject\s+alpha\b'
                elif term == "project beta":
                    pattern = r'\bproject\s+beta\b'
                elif term == "enterprise knowledge base":
                    pattern = r'\benterprise\s+knowledge\s+base\b'

                if re.search(pattern, text_lower):
                    key = (category, term)
                    if key not in found:
                        # Find original casing in text if possible
                        original_match = re.search(pattern, text, re.IGNORECASE)
                        name = original_match.group(0) if original_match else term.title()
                        
                        confidence = 0.95 if category in ("Programming Languages", "Frameworks") else 0.85
                        entities.append(EntityNode(
                            name=name,
                            category=category,
                            confidence=confidence
                        ))
                        found.add(key)

        # 2. General Name pattern heuristics (e.g. "by [Author]")
        author_match = re.search(r'(?:author|by):\s*([a-zA-Z\s]+)', text, re.IGNORECASE)
        if author_match:
            name = author_match.group(1).strip()
            if len(name) < 40 and ("People", name.lower()) not in found:
                entities.append(EntityNode(
                    name=name,
                    category="People",
                    confidence=0.8
                ))
                found.add(("People", name.lower()))

        # 3. Date pattern extraction (Years)
        years = re.findall(r'\b(19\d{2}|20\d{2})\b', text)
        for y in years:
            key = ("Date", y)
            if key not in found:
                entities.append(EntityNode(
                    name=y,
                    category="Date",
                    confidence=0.9
                ))
                found.add(key)

        # 4. Standard file references
        files = re.findall(r'\b[\w\-]+\.(?:docx|pdf|txt|md|csv|json)\b', text_lower)
        for f in files:
            key = ("Documents", f)
            if key not in found:
                entities.append(EntityNode(
                    name=f,
                    category="Documents",
                    confidence=0.9
                ))
                found.add(key)

        return entities
