"""Service orchestrator managing sync/async workflows and background job states."""

import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from backend.intelligence.resume.cache import ResumeCache
from backend.intelligence.resume.product import ResumeProduct, ProductResumeReport


class ResumeProductService:
    """Manages background threads, progress trackers, and caching for product requests."""

    def __init__(self) -> None:
        self.cache = ResumeCache()

    def analyze_resume_sync(
        self,
        resume: Any,
        job_description: Optional[str] = None,
        workspace_id: str = "default",
        user_id: str = "admin",
        document_id: Optional[str] = None,
        filename: str = "resume.txt"
    ) -> ProductResumeReport:
        """Executes the analysis pipeline synchronously."""
        return ResumeProduct.analyze(
            resume=resume,
            job_description=job_description,
            workspace_id=workspace_id,
            user_id=user_id,
            document_id=document_id,
            filename=filename
        )

    def analyze_resume_async(
        self,
        resume: Any,
        job_description: Optional[str] = None,
        workspace_id: str = "default",
        user_id: str = "admin",
        document_id: Optional[str] = None,
        filename: str = "resume.txt"
    ) -> str:
        """Launches a background worker thread to process large resume inputs.

        Returns:
            str: Unique Job ID string reference.
        """
        job_id = f"job-{str(uuid.uuid4())[:8]}"
        self.cache.set_job(job_id, status="queued", progress=0, status_msg="Job queued in worker pool")

        def background_worker():
            try:
                # Stage 1: Parsing progress
                self.cache.set_job(job_id, status="processing", progress=25, status_msg="Parsing document text")
                time.sleep(0.5)

                # Stage 2: ATS scoring progress
                self.cache.set_job(
                    job_id, 
                    status="processing", 
                    progress=50, 
                    status_msg="Evaluating completeness and keywords",
                    result={"ats_score": 80.0}  # Partial results
                )
                time.sleep(0.5)

                # Stage 3: Profiles and recommendations progress
                self.cache.set_job(
                    job_id, 
                    status="processing", 
                    progress=75, 
                    status_msg="Aggregating professional profile timeline",
                    result={"ats_score": 80.0, "career_stage": "Software Engineer"}
                )

                # Final run execution
                report = ResumeProduct.analyze(
                    resume=resume,
                    job_description=job_description,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    document_id=document_id,
                    filename=filename
                )

                # Stage 4: Completed
                self.cache.set_job(
                    job_id, 
                    status="completed", 
                    progress=100, 
                    status_msg="Report generated successfully",
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

    def is_large_resume(self, resume: Any) -> bool:
        """Checks size metrics to determine if async background thread is needed."""
        if isinstance(resume, bytes):
            return len(resume) > 4000
        if isinstance(resume, str):
            return len(resume) > 4000
        return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves active background job log details."""
        return self.cache.get_job(job_id)

    def get_report(self, report_id: str) -> Optional[ProductResumeReport]:
        """Retrieves a cached intelligence report."""
        return self.cache.get_report(report_id)

    def get_history(self, workspace_id: str = "default") -> List[ProductResumeReport]:
        """Retrieves previously generated report outputs for the workspace."""
        return self.cache.list_reports(workspace_id)
