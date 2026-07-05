"""Aggregates chunk parsing, entity mapping, and summaries into unified reports."""

import uuid
from datetime import datetime
from typing import Dict, List, Any
from backend.intelligence.document.document_model import (
    DocumentAnalysisReport,
    DocumentMetadata,
    SummaryDetail,
    Topic,
    Entity,
    Citation,
    SimilarityMapping,
    ExtractedKnowledgeItem
)


class DocumentReportBuilder:
    """Assembles analytical results into strongly typed DocumentAnalysisReport profiles."""

    def build_report(
        self,
        workspace_id: str,
        document_ids: List[str],
        metadata: Dict[str, DocumentMetadata],
        summary: SummaryDetail,
        topics: List[Topic],
        entities: List[Entity],
        citations: List[Citation],
        similar_documents: List[SimilarityMapping],
        extracted_knowledge: List[ExtractedKnowledgeItem]
    ) -> DocumentAnalysisReport:
        """Assembles and generates a fresh analysis report model.

        Args:
            workspace_id: Associated tenant workspace ID.
            document_ids: Ingested document reference IDs.
            metadata: Map of document metadata items.
            summary: Multidimensional summarization model.
            topics: Extracted main themes list.
            entities: Extracted vocabulary items list.
            citations: Source context matching pointers.
            similar_documents: Cross-document relationship mapping.
            extracted_knowledge: Profile integration knowledge items.

        Returns:
            DocumentAnalysisReport: Structured report envelope.
        """
        report_id = f"rep-doc-{str(uuid.uuid4())[:8]}"
        
        return DocumentAnalysisReport(
            report_id=report_id,
            workspace_id=workspace_id,
            document_ids=document_ids,
            metadata=metadata,
            summary=summary,
            topics=topics,
            entities=entities,
            citations=citations,
            similar_documents=similar_documents,
            extracted_knowledge=extracted_knowledge,
            analyzed_at=datetime.utcnow()
        )
