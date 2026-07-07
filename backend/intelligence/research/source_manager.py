"""Manages raw and parsed research paper source entities."""

from typing import Dict, List, Optional
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.research.models import ResearchPaperMetadata
from backend.intelligence.research.paper_parser import PaperParser


class SourceManager:
    """Retrieves uploaded document contents and coordinates metadata parses."""

    def __init__(self) -> None:
        self.doc_cache = DocumentCache()
        self.parser = PaperParser()

    def get_sources_metadata(
        self,
        workspace_id: str,
        document_ids: List[str]
    ) -> List[ResearchPaperMetadata]:
        """Loads raw text contents and extracts structured metadata for each source paper."""
        # Retrieve raw contents from Document Intelligence Cache
        raw_docs = self.doc_cache.get_documents_by_ids(document_ids)
        
        parsed_papers = []
        for doc_id, (filename, content) in raw_docs.items():
            metadata = self.parser.parse_paper_text(doc_id, content)
            parsed_papers.append(metadata)
            
        return parsed_papers
