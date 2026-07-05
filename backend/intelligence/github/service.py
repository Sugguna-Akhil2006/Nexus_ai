"""Service orchestrator managing sync/async workflows and background job states for GitHub."""

import threading
import time
import uuid
import os
from typing import Any, Dict, List, Optional

from backend.intelligence.github.cache import GitHubCache
from backend.intelligence.github.product import GitHubProduct
from backend.intelligence.github.models import GitHubIntelligenceReport


class GitHubProductService:
    """Manages background threads, progress trackers, and caching for GitHub product requests."""

    def __init__(self) -> None:
        self.cache = GitHubCache()

    def analyze_sync(
        self,
        repository_url: Optional[str] = None,
        username: Optional[str] = None,
        organization: Optional[str] = None,
        workspace_id: str = "default-ws",
        user_id: str = "admin",
        branch: str = "main",
        options: Optional[Dict[str, Any]] = None
    ) -> GitHubIntelligenceReport:
        """Executes the GitHub analysis pipeline synchronously."""
        return GitHubProduct.analyze(
            repository_url=repository_url,
            username=username,
            organization=organization,
            workspace_id=workspace_id,
            user_id=user_id,
            branch=branch,
            options=options
        )

    def analyze_async(
        self,
        repository_url: Optional[str] = None,
        username: Optional[str] = None,
        organization: Optional[str] = None,
        workspace_id: str = "default-ws",
        user_id: str = "admin",
        branch: str = "main",
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Launches a background worker thread to process large GitHub inputs.

        Returns:
            str: Unique Job ID string reference.
        """
        job_id = f"job-git-{str(uuid.uuid4())[:8]}"
        self.cache.set_job(job_id, status="queued", progress=0, status_msg="GitHub job queued in worker pool")

        def background_worker():
            try:
                # Stage 1: Loading repository progress
                self.cache.set_job(job_id, status="processing", progress=25, status_msg="Loading and crawling repository files")
                time.sleep(0.5)

                # Stage 2: Quality & Dependency checks progress
                self.cache.set_job(
                    job_id, 
                    status="processing", 
                    progress=50, 
                    status_msg="Performing code quality audit & parsing dependency manifests",
                    result={"progress": 50}
                )
                time.sleep(0.5)

                # Stage 3: Health timelines checks progress
                self.cache.set_job(
                    job_id, 
                    status="processing", 
                    progress=75, 
                    status_msg="Aggregating git commit timelines, release tags & collaboration stats",
                    result={"progress": 75}
                )

                # Final run execution
                report = GitHubProduct.analyze(
                    repository_url=repository_url,
                    username=username,
                    organization=organization,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    branch=branch,
                    options=options
                )

                # Stage 4: Completed
                self.cache.set_job(
                    job_id, 
                    status="completed", 
                    progress=100, 
                    status_msg="GitHub engineering report generated successfully",
                    report_id=report.report_id,
                    result=report.model_dump()
                )
            except Exception as e:
                self.cache.set_job(
                    job_id, 
                    status="failed", 
                    progress=100, 
                    status_msg=f"Execution failed: {str(e)}"
                )

        thread = threading.Thread(target=background_worker, daemon=True)
        thread.start()
        return job_id

    def is_large_repository(self, target_path: str) -> bool:
        """Checks size metrics to determine if async background thread is needed."""
        if not target_path or not os.path.exists(target_path) or not os.path.isdir(target_path):
            return False
            
        file_count = 0
        for _, _, files in os.walk(target_path):
            file_count += len(files)
            if file_count > 150:  # Threshold for considering it large
                return True
        return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active background job log details."""
        return self.cache.get_job(job_id)

    def get_report(self, report_id: str) -> Optional[GitHubIntelligenceReport]:
        """Retrieves a cached intelligence report."""
        return self.cache.get_report(report_id)

    def get_history(self, workspace_id: str = "default-ws") -> List[GitHubIntelligenceReport]:
        """Retrieves previously generated report outputs for the workspace."""
        return self.cache.list_reports(workspace_id)
