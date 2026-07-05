"""FastAPI endpoint declarations for document ingestion, analysis, querying, and comparisons."""

from typing import Any, List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from backend.intelligence.document.document_model import (
    UploadResponse,
    AnalyzeRequest,
    QueryRequest,
    QueryResponse,
    DocumentAnalysisReport
)
from backend.intelligence.document.document_service import DocumentProductService

router = APIRouter(prefix="/document", tags=["document"])
product_service = DocumentProductService()


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> Any:
    """Ingests file contents and stores raw bytes in workspace cache."""
    try:
        content = file.file.read()
        return product_service.upload_document(file.filename, content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze")
def analyze_documents(req: AnalyzeRequest) -> Any:
    """Initiates synchronous or asynchronous processing pipelines."""
    try:
        is_async = req.options.get("async") is True if req.options else False
        
        if is_async:
            job_id = product_service.analyze_async(
                workspace_id=req.workspace_id,
                document_ids=req.document_ids,
                options=req.options
            )
            return {
                "job_id": job_id,
                "status": "processing",
                "progress": 10,
                "status_msg": "Analysis queued"
            }
        else:
            report = product_service.analyze_sync(
                workspace_id=req.workspace_id,
                document_ids=req.document_ids,
                options=req.options
            )
            return report.model_dump()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")


@router.post("/query", response_model=QueryResponse)
def query_documents(req: QueryRequest) -> Any:
    """Performs sliding-window citation-aware query mapping."""
    try:
        return product_service.query_documents(
            workspace_id=req.workspace_id,
            document_ids=req.document_ids,
            query=req.query,
            options=req.options
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document query failed: {str(e)}")


@router.get("/report/{report_id}", response_model=DocumentAnalysisReport)
def get_report(report_id: str) -> Any:
    """Retrieves document analysis report from history db."""
    report = product_service.history_manager.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Document report '{report_id}' not found.")
    return report


@router.get("/status/{job_id}")
def get_job_status(job_id: str) -> Any:
    """Checks the progress status of a queued background thread job."""
    job = product_service.cache.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Background analysis job '{job_id}' not found.")
    return job


@router.get("/history")
def get_history(workspace_id: str = Query(..., description="Workspace ID scope filter")) -> Any:
    """Retrieves document analysis report history log list."""
    try:
        reports = product_service.history_manager.list_history(workspace_id)
        return {"history": [r.model_dump() for r in reports]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History query failed: {str(e)}")


@router.get("/compare")
def compare_reports(base_id: str = Query(...), target_id: str = Query(...)) -> Any:
    """Computes comparison differentials between base and target reports."""
    base = product_service.history_manager.get_report(base_id)
    target = product_service.history_manager.get_report(target_id)
    
    if not base or not target:
        raise HTTPException(status_code=404, detail="One or both comparison reports not found in history DB.")
        
    try:
        return product_service.history_manager.compare_reports(base, target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report comparison failed: {str(e)}")
