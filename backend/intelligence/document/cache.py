"""Thread-safe in-memory cache for jobs, reports, documents, and profiles."""

import threading
from typing import Dict, List, Optional, Any, Tuple


class DocumentCache:
    """Manages concurrent read/write state for background jobs, profiles, and reports."""

    _instance: Optional["DocumentCache"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "DocumentCache":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._lock: threading.RLock = threading.RLock()
            self._jobs: Dict[str, Dict[str, Any]] = {}
            self._reports: Dict[str, Any] = {}
            self._profiles: Dict[str, Any] = {}
            self._documents: Dict[str, Tuple[str, str]] = {}  # doc_id -> (filename, content)
            self._initialized = True

    def set_job(self, job_id: str, data: Dict[str, Any]) -> None:
        """Sets status values for a background thread execution job."""
        with self._lock:
            self._jobs[job_id] = data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a background job status."""
        with self._lock:
            return self._jobs.get(job_id)

    def set_report(self, report_id: str, report: Any) -> None:
        """Caches a processed DocumentAnalysisReport."""
        with self._lock:
            self._reports[report_id] = report

    def get_report(self, report_id: str) -> Optional[Any]:
        """Retrieves a cached report by ID."""
        with self._lock:
            return self._reports.get(report_id)

    def set_profile(self, user_id: str, profile: Any) -> None:
        """Caches a user's canonical KnowledgeProfile."""
        with self._lock:
            self._profiles[user_id] = profile

    def get_profile(self, user_id: str) -> Optional[Any]:
        """Retrieves a cached KnowledgeProfile."""
        with self._lock:
            return self._profiles.get(user_id)

    def save_document(self, document_id: str, filename: str, content: str) -> None:
        """Saves raw document contents for query citation matching."""
        with self._lock:
            self._documents[document_id] = (filename, content)

    def get_document(self, document_id: str) -> Optional[Tuple[str, str]]:
        """Retrieves raw document metadata and text content."""
        with self._lock:
            return self._documents.get(document_id)

    def get_documents_by_ids(self, document_ids: List[str]) -> Dict[str, Tuple[str, str]]:
        """Gets multiple document records."""
        with self._lock:
            return {
                doc_id: self._documents[doc_id]
                for doc_id in document_ids
                if doc_id in self._documents
            }
