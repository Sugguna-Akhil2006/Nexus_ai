"""Thread-safe in-memory cache for GitHub reports, profiles, and background jobs."""

import threading
from typing import Any, Dict, List, Optional


class GitHubCache:
    """Thread-safe singleton caching job details, profiles, and GitHub intelligence reports."""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "GitHubCache":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._jobs = {}
                cls._instance._reports = {}
                cls._instance._profiles = {}
                cls._instance._lock = threading.RLock()
            return cls._instance

    def set_job(self, job_id: str, status: str, progress: int, status_msg: str = "", report_id: Optional[str] = None, result: Optional[Any] = None) -> None:
        """Stores or updates status details for an active background execution job."""
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "status": status,
                "progress": progress,
                "status_msg": status_msg,
                "report_id": report_id,
                "result": result
            }

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves background job progress and status details."""
        with self._lock:
            return self._jobs.get(job_id)

    def set_report(self, report_id: str, report: Any) -> None:
        """Saves a compiled GitHub Intelligence Report to cache."""
        with self._lock:
            self._reports[report_id] = report

    def get_report(self, report_id: str) -> Optional[Any]:
        """Retrieves a previously cached intelligence report."""
        with self._lock:
            return self._reports.get(report_id)

    def list_reports(self, workspace_id: str = "default") -> List[Any]:
        """Lists all reports under a workspace."""
        with self._lock:
            return [
                r for r in self._reports.values()
                if getattr(r, "workspace_id", "") == workspace_id or r.workspace_id == workspace_id
            ]

    def set_profile(self, user_id: str, profile: Any) -> None:
        """Updates user's canonical KnowledgeProfile record."""
        with self._lock:
            self._profiles[user_id] = profile

    def get_profile(self, user_id: str) -> Optional[Any]:
        """Retrieves a cached KnowledgeProfile."""
        with self._lock:
            return self._profiles.get(user_id)
