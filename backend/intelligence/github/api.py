"""FastAPI REST endpoints for the GitHub Intelligence Product Integration."""

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status, Response

from backend.intelligence.github.report_renderer import GitHubReportRenderer

from backend.intelligence.github.service import GitHubProductService
from backend.intelligence.github.history import GitHubHistoryManager
from backend.intelligence.github.controller import (
    AnalyzeRequest,
    RepositoryRequest,
    UserRequest,
    JobStatusResponse
)


router = APIRouter(prefix="/github", tags=["GitHub Product"])
product_service = GitHubProductService()
history_manager = GitHubHistoryManager()


@router.post("/analyze")
def analyze_github(req: AnalyzeRequest) -> Any:
    """Orchestrates sync/async repository, username, or organization analysis."""
    try:
        # Determine if async analysis is needed
        target_path = req.repository_url or "."
        is_large = product_service.is_large_repository(target_path)
        
        # Overrides from options
        if req.options and req.options.get("async") is True:
            is_large = True

        if is_large:
            job_id = product_service.analyze_async(
                repository_url=req.repository_url,
                username=req.username,
                organization=req.organization,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                branch=req.branch,
                options=req.options
            )
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 25,
                "status_msg": "GitHub analysis queued in background worker pool"
            }
        else:
            report = product_service.analyze_sync(
                repository_url=req.repository_url,
                username=req.username,
                organization=req.organization,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                branch=req.branch,
                options=req.options
            )
            # Persist report in SQL history
            history_manager.save_report(report, req.workspace_id)
            return report.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis initiation failed: {str(e)}")


@router.post("/repository")
def analyze_repository(req: RepositoryRequest) -> Any:
    """Initiates quality and timeline scanning for a target repository URL or workspace folder."""
    try:
        is_large = product_service.is_large_repository(req.repository_url)
        if req.options and req.options.get("async") is True:
            is_large = True

        if is_large:
            job_id = product_service.analyze_async(
                repository_url=req.repository_url,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                branch=req.branch,
                options=req.options
            )
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 25,
                "status_msg": "GitHub repository analysis queued"
            }
        else:
            report = product_service.analyze_sync(
                repository_url=req.repository_url,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                branch=req.branch,
                options=req.options
            )
            history_manager.save_report(report, req.workspace_id)
            return report.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")


@router.post("/user")
def analyze_user(req: UserRequest) -> Any:
    """Performs developer profile analysis based on public commits and repository contributions."""
    try:
        # Run user analysis (treated as sync unless explicitly requested async)
        is_large = req.options.get("async") is True if req.options else False

        if is_large:
            job_id = product_service.analyze_async(
                username=req.username,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                options=req.options
            )
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 25,
                "status_msg": "GitHub developer profile analysis queued"
            }
        else:
            report = product_service.analyze_sync(
                username=req.username,
                workspace_id=req.workspace_id,
                user_id=req.user_id,
                options=req.options
            )
            history_manager.save_report(report, req.workspace_id)
            return report.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"User profile analysis failed: {str(e)}")


@router.get("/report/{id}")
def get_report(id: str, export: Optional[str] = Query(None, description="Export format: pdf, html, markdown, or json")) -> Any:
    """Retrieves compiled reports by unique report ID or checks active background job status."""
    # 1. Check if ID represents a background job status
    job = product_service.get_job_status(id)
    if job:
        return job

    # 2. Check cache first
    report = product_service.get_report(id)
    if not report:
        # Check SQLite SQL database history tables
        report = history_manager.get_report(id)

    if not report:
        raise HTTPException(status_code=404, detail=f"GitHub report or job status with ID '{id}' not found.")

    # Handle exports formatting using GitHubReportRenderer
    renderer = GitHubReportRenderer()
    if export == "pdf":
        pdf_bytes = renderer.to_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=github_report_{id}.pdf"}
        )
    elif export == "html":
        html_str = renderer.to_html(report)
        return Response(
            content=html_str.encode("utf-8"),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename=github_report_{id}.html"}
        )
    elif export == "markdown" or export == "md":
        md_str = renderer.to_markdown(report)
        return Response(
            content=md_str.encode("utf-8"),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename=github_report_{id}.md"}
        )

    return report.model_dump()


@router.get("/history")
def get_history(workspace_id: str = "default-ws") -> Any:
    """Lists previous engineering reports details and timeline metrics."""
    reports = history_manager.get_history(workspace_id)
    return {"history": [rep.model_dump() for rep in reports]}


@router.get("/status/{execution_id}")
def get_status(execution_id: str) -> Any:
    """Endpoint query interface for async tracking status progress details."""
    job = product_service.get_job_status(execution_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"No background job execution with ID '{execution_id}' matches.")
    return job
