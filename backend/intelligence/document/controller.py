"""Controller layer delegating raw inputs to service logic and verifying validation gates."""

import hashlib
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from backend.intelligence.document.service import DocumentProductService
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.models import DocumentKnowledgeReport
from backend.intelligence.document.document_model import UploadResponse, QueryResponse
from backend.intelligence.document.workflow import DocumentStageNames, StageExecutionError


class DocumentProductController:
    """Delegates routes to services, handles parameter validations, and computes upload models."""

    def __init__(self) -> None:
        self.service = DocumentProductService()
        self.cache = DocumentCache()

    def upload_document(self, filename: str, content_bytes: bytes) -> UploadResponse:
        """Parses document format extension, safely decodes text, and caches it."""
        if not content_bytes:
            raise StageExecutionError(DocumentStageNames.LOADER, "Uploaded file content is empty.")

        # Extract format
        _, ext = os.path.splitext(filename.lower())
        fmt = ext.upper().lstrip(".")
        if not fmt:
            fmt = "TXT"

        # Conversion simulation for binary formats
        if fmt in ("PDF", "DOCX", "PPTX", "XLSX"):
            text_content = f"--- Document Name: {filename} ---\nThis is parsed text extraction content simulating a {fmt} file structure.\nContains technical details regarding Python, React, and FastAPI schemas."
        else:
            try:
                text_content = content_bytes.decode("utf-8", errors="ignore")
            except Exception:
                text_content = f"Binary contents of file {filename}."

        doc_id = f"doc-{str(uuid.uuid4())[:8]}"
        checksum = hashlib.sha256(content_bytes).hexdigest()
        
        # Save to cache
        self.cache.save_document(doc_id, filename, text_content)

        return UploadResponse(
            document_id=doc_id,
            filename=filename,
            mime_type=f"application/{fmt.lower()}",
            file_size=len(content_bytes),
            checksum=checksum,
            uploaded_at=datetime.utcnow()
        )

    def analyze(
        self,
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Triggers sync/async pipeline based on options."""
        opts = options or {}
        is_async = opts.get("async", False) or opts.get("is_async", False)

        if is_async:
            job_id = self.service.analyze_async(workspace_id, document_ids, user_id, opts)
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 0,
                "status_msg": "Analysis job initialized in background"
            }
        else:
            return self.service.analyze_sync(workspace_id, document_ids, user_id, opts)

    def query(
        self,
        workspace_id: str,
        document_ids: List[str],
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
        """Delegates cross-document query search."""
        return self.service.query_documents(workspace_id, document_ids, query, options)

    def compare(self, base_id: str, target_id: str) -> Dict[str, Any]:
        """Compares base vs target report metadata."""
        return self.service.compare_reports(base_id, target_id)

    def get_report(self, report_id: str) -> Optional[DocumentKnowledgeReport]:
        """Retrieves single report."""
        return self.service.get_report(report_id)

    def get_history(self, workspace_id: str) -> List[Any]:
        """Lists reports history."""
        return self.service.get_history(workspace_id)

    def get_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves background job status logs."""
        return self.service.get_job_status(execution_id)
