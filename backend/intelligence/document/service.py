"""Service orchestrator managing sync/async workflows and background job states for Documents."""

import time
import uuid
import threading
from typing import Any, Dict, List, Optional

from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.product import DocumentProduct
from backend.intelligence.document.history import DocumentHistoryManager
from backend.intelligence.document.models import DocumentKnowledgeReport
from backend.intelligence.document.document_model import QueryResponse
from backend.intelligence.document.document_agent import DocumentAgent


class DocumentProductService:
    """Manages background worker thread pools, history lookups, and search querying."""

    def __init__(self) -> None:
        self.cache = DocumentCache()
        self.history_manager = DocumentHistoryManager()
        self.agent = DocumentAgent()

    def analyze_sync(
        self,
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentKnowledgeReport:
        """Executes the Document reasoning pipeline synchronously."""
        return DocumentProduct.analyze(
            workspace_id=workspace_id,
            document_ids=document_ids,
            user_id=user_id,
            options=options
        )

    def analyze_async(
        self,
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Launches a background worker thread to process large document collections.

        Returns:
            str: Unique Job ID / Execution ID.
        """
        execution_id = f"job-doc-{str(uuid.uuid4())[:8]}"
        self.cache.set_job(execution_id, status="queued", progress=0, status_msg="Document workflow job queued in worker pool")

        def background_worker():
            try:
                # Stage 1: Loading & Ingestion
                self.cache.set_job(execution_id, status="processing", progress=25, status_msg="Loading and parsing document collection")
                time.sleep(0.2)

                # Stage 2: Deep Graph reasoning
                self.cache.set_job(execution_id, status="processing", progress=50, status_msg="Extracting entities and building knowledge graphs")
                time.sleep(0.2)

                # Stage 3: Summary & Citations
                self.cache.set_job(execution_id, status="processing", progress=75, status_msg="Synthesizing executive summaries and matching citation references")
                time.sleep(0.2)

                # Execute pipeline
                report = DocumentProduct.analyze(
                    workspace_id=workspace_id,
                    document_ids=document_ids,
                    user_id=user_id,
                    options=options
                )

                # Completed
                self.cache.set_job(
                    execution_id,
                    status="completed",
                    progress=100,
                    status_msg="Document intelligence report generated successfully",
                    report_id=report.report_id,
                    result=report.model_dump()
                )
            except Exception as e:
                self.cache.set_job(
                    execution_id,
                    status="failed",
                    progress=100,
                    status_msg=f"Execution stage failure: {str(e)}"
                )

        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        return execution_id

    def get_job_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves background progress details."""
        return self.cache.get_job(execution_id)

    def get_report(self, report_id: str) -> Optional[DocumentKnowledgeReport]:
        """Retrieves report from cache or database."""
        report = self.cache.get_report(report_id)
        if not report:
            report = self.history_manager.get_knowledge_report(report_id)
        return report

    def get_history(self, workspace_id: str) -> List[Any]:
        """Lists historical reports."""
        return self.history_manager.list_history(workspace_id)

    def compare_reports(self, base_id: str, target_id: str) -> Dict[str, Any]:
        """Compares base and target reports."""
        base = self.get_report(base_id)
        target = self.get_report(target_id)
        if not base or not target:
            raise ValueError("Base or target report not found in history DB.")
        return self.history_manager.compare_reports(base, target)

    def query_documents(
        self,
        workspace_id: str,
        document_ids: List[str],
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
        """Runs citation-backed semantic Q&A queries across active documents."""
        opts = options or {}
        doc_chunks = {}
        doc_names = {}
        
        documents = self.cache.get_documents_by_ids(document_ids)
        for doc_id, (filename, content) in documents.items():
            doc_names[doc_id] = filename
            # Quick split-based fallback chunking
            from backend.intelligence.document.chunk_manager import TextChunk
            chunks = [
                TextChunk(
                    chunk_id=f"{doc_id}-{idx}",
                    text=content[i:i+800],
                    section="General",
                    start_char=i,
                    end_char=i+len(content[i:i+800])
                )
                for idx, i in enumerate(range(0, len(content), 650))
            ]
            doc_chunks[doc_id] = chunks

        answer, citations = self.agent.query_documents(
            query=query,
            document_chunks=doc_chunks,
            document_names=doc_names,
            limit=opts.get("limit", 3)
        )

        return QueryResponse(
            query=query,
            answer=answer,
            citations=citations
        )

    def search_semantic_index(self, report_id: str, search_type: str, query: str) -> List[str]:
        """Queries the compiled semantic index of a processed document report."""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Knowledge report '{report_id}' not found.")
        
        from backend.intelligence.document.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        return processor.semantic_index_builder.search_index(
            report.semantic_index, search_type, query
        )

