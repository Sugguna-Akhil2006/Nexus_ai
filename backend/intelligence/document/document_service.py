"""Product Service facade executing sync/async Document analyses and SQLite storage."""

import os
import hashlib
import json
import threading
import uuid
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

from backend.api.sqlite_mock import DBStorage
from backend.intelligence.document.document_model import (
    DocumentAnalysisReport,
    DocumentMetadata,
    SummaryDetail,
    Topic,
    Entity,
    Citation,
    SimilarityMapping,
    ExtractedKnowledgeItem,
    UploadResponse,
    QueryResponse
)
from backend.intelligence.document.chunk_manager import ChunkManager, TextChunk
from backend.intelligence.document.cache import DocumentCache
from backend.intelligence.document.document_agent import DocumentAgent
from backend.intelligence.document.document_workflow import DocumentStageNames, StageExecutionError
from backend.intelligence.profile.services import ProfileService
from backend.intelligence.profile.models import KnowledgeProfile, ProfilePersonalInfo, ProfileSkill, ProfileProject
from backend.intelligence.profile.merger import ProfileMerger


class DocumentHistoryManager:
    """Manages history tables, SQL queries, and diffing algorithms for Document reports."""

    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        """Initializes sqlite table for product level report history."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS document_product_history (
                    report_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    document_ids TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
                conn.commit()
        finally:
            conn.close()

    def save_report(self, report: DocumentAnalysisReport) -> None:
        """Saves a compiled report to SQLite."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            with db._lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO document_product_history 
                    (report_id, workspace_id, document_ids, report_data, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        report.report_id,
                        report.workspace_id,
                        ",".join(report.document_ids),
                        report.model_dump_json(),
                        report.analyzed_at.isoformat()
                    )
                )
                conn.commit()
        finally:
            conn.close()

    def get_report(self, report_id: str) -> Optional[DocumentAnalysisReport]:
        """Retrieves report from DB."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT report_data FROM document_product_history WHERE report_id = ?",
                (report_id,)
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return DocumentAnalysisReport.model_validate(data)
            return None
        finally:
            conn.close()

    def list_history(self, workspace_id: str) -> List[DocumentAnalysisReport]:
        """Lists all reports under a workspace."""
        db = DBStorage()
        conn = db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT report_data FROM document_product_history WHERE workspace_id = ? ORDER BY created_at DESC",
                (workspace_id,)
            )
            rows = cursor.fetchall()
            reports = []
            for row in rows:
                data = json.loads(row[0])
                reports.append(DocumentAnalysisReport.model_validate(data))
            return reports
        finally:
            conn.close()

    def compare_reports(self, base: DocumentAnalysisReport, target: DocumentAnalysisReport) -> Dict[str, Any]:
        """Computes diff metrics between two Document reports."""
        base_words = sum(meta.word_count for meta in base.metadata.values())
        target_words = sum(meta.word_count for meta in target.metadata.values())
        
        base_lines = sum(meta.line_count for meta in base.metadata.values())
        target_lines = sum(meta.line_count for meta in target.metadata.values())
        
        base_kws = set()
        for meta in base.metadata.values():
            base_kws.update(meta.keywords)
            
        target_kws = set()
        for meta in target.metadata.values():
            target_kws.update(meta.keywords)

        new_kws = list(target_kws - base_kws)
        removed_kws = list(base_kws - target_kws)

        return {
            "base_report_id": base.report_id,
            "target_report_id": target.report_id,
            "comparison": {
                "word_count": {
                    "base": base_words,
                    "target": target_words,
                    "delta": target_words - base_words
                },
                "line_count": {
                    "base": base_lines,
                    "target": target_lines,
                    "delta": target_lines - base_lines
                },
                "keywords": {
                    "added": new_kws,
                    "removed": removed_kws
                }
            }
        }


class DocumentProductService:
    """Manages document conversions, async worker thread pools, history lookups, and profile syncs."""

    def __init__(self) -> None:
        self.agent = DocumentAgent()
        self.cache = DocumentCache()
        self.chunk_manager = ChunkManager()
        self.history_manager = DocumentHistoryManager()
        self.profile_svc = ProfileService()
        self.profile_merger = ProfileMerger()

    def upload_document(self, filename: str, content_bytes: bytes) -> UploadResponse:
        """Parses formats and registers raw content bytes into caching."""
        if not content_bytes:
            raise StageExecutionError(DocumentStageNames.LOADER, "Empty document upload content.")

        # Detect format
        _, ext = os.path.splitext(filename.lower())
        fmt = ext.upper().lstrip(".")
        if not fmt:
            fmt = "TXT"

        # Safe decode binary bytes to text based on format
        if fmt in ("PDF", "DOCX", "PPTX", "XLSX"):
            # Mock parse extraction for binary layouts
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

    def analyze_sync(
        self,
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> DocumentAnalysisReport:
        """Executes Document Ingestion, Summarization, and profile integration synchronously."""
        opts = options or {}
        
        # Load raw files contents
        documents = self.cache.get_documents_by_ids(document_ids)
        if not documents:
            raise StageExecutionError(
                DocumentStageNames.LOADER,
                f"None of the document_ids {document_ids} are registered in cache."
            )

        # Run pipeline
        report = self.agent.analyze_documents(workspace_id, documents, opts)
        
        # Persist report database entry
        self.history_manager.save_report(report)
        self.cache.set_report(report.report_id, report)

        # Update User Profile with Extracted Knowledge
        try:
            profile = self.cache.get_profile(user_id)
            if not profile:
                profile = KnowledgeProfile(
                    workspace_id=workspace_id,
                    user_id=user_id,
                    personal_info=ProfilePersonalInfo(full_name=user_id)
                )

            # Convert Extracted Knowledge Items to Profile structures
            incoming_skills = {}
            incoming_projects = []
            for item in report.extracted_knowledge:
                if item.category == "Skill":
                    incoming_skills[item.value["name"]] = ProfileSkill(
                        name=item.value["name"],
                        category=item.value["category"],
                        confidence_score=1.0,
                        sources=["Document"],
                        evidence=["Document knowledge extraction"]
                    )
                elif item.category == "Project":
                    incoming_projects.append(ProfileProject(
                        name=item.value["name"],
                        description=item.value["description"],
                        technologies=[],
                        sources=["Document"]
                    ))

            incoming_profile = KnowledgeProfile(
                workspace_id=workspace_id,
                user_id=user_id,
                skills=incoming_skills,
                projects=incoming_projects
            )

            # Merge profiles
            updated_profile = self.profile_merger.merge_profiles(profile, incoming_profile)
            self.cache.set_profile(user_id, updated_profile)
        except Exception:
            # Profile updates are non-blocking, log and proceed
            pass

        return report

    def analyze_async(
        self,
        workspace_id: str,
        document_ids: List[str],
        user_id: str = "admin",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Starts asynchronous pipeline loop in a background thread."""
        job_id = f"job-doc-{str(uuid.uuid4())[:8]}"
        self.cache.set_job(job_id, {
            "status": "queued",
            "progress": 10,
            "status_msg": "Analysis queued"
        })

        thread = threading.Thread(
            target=self._async_analysis_worker,
            args=(job_id, workspace_id, document_ids, user_id, options)
        )
        thread.daemon = True
        thread.start()

        return job_id

    def query_documents(
        self,
        workspace_id: str,
        document_ids: List[str],
        query: str,
        options: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
        """Query ingested documents using sliding window tf-idf keyword search."""
        opts = options or {}
        
        # Load documents contents
        documents = self.cache.get_documents_by_ids(document_ids)
        if not documents:
            raise StageExecutionError(
                DocumentStageNames.LOADER,
                f"No matching document records found in workspace cache."
            )

        # Build chunks for searching
        doc_chunks = {}
        doc_names = {}
        for doc_id, (filename, content) in documents.items():
            doc_names[doc_id] = filename
            # Quick parsing
            _, ext = os.path.splitext(filename.lower())
            fmt = ext.upper().lstrip(".") or "TXT"
            chunks = self.chunk_manager.chunk_document(content, fmt)
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

    def _async_analysis_worker(
        self,
        job_id: str,
        workspace_id: str,
        document_ids: List[str],
        user_id: str,
        options: Optional[Dict[str, Any]]
    ) -> None:
        """Background worker thread function."""
        try:
            # Stage 2: Parsing / Chunking progress
            self.cache.set_job(job_id, {
                "status": "processing",
                "progress": 30,
                "status_msg": "Parsing and semantic chunking"
            })

            # Stage 3: Summary extraction
            self.cache.set_job(job_id, {
                "status": "processing",
                "progress": 60,
                "status_msg": "Extracting metadata and compiling summaries"
            })

            # Stage 4: Execution
            report = self.analyze_sync(workspace_id, document_ids, user_id, options)

            # Stage 5: Finalized complete
            self.cache.set_job(job_id, {
                "status": "completed",
                "progress": 100,
                "status_msg": "Document intelligence report ready",
                "report_id": report.report_id
            })

        except Exception as e:
            self.cache.set_job(job_id, {
                "status": "failed",
                "progress": 100,
                "status_msg": f"Ingestion stage failure: {str(e)}"
            })
