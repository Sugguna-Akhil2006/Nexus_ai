"""FastAPI endpoints for deep Document processing, uploads, querying, and comparisons."""

from typing import Any, List, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Query

from backend.intelligence.document.controller import DocumentProductController
from backend.intelligence.document.document_model import (
    UploadResponse,
    AnalyzeRequest,
    QueryRequest,
    QueryResponse,
    DocumentAnalysisReport
)
from backend.intelligence.document.models import (
    DocumentKnowledgeReport,
    ProcessRequest,
    SearchIndexRequest
)

router = APIRouter(prefix="/document", tags=["document"])
controller = DocumentProductController()


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)) -> Any:
    """Ingests file contents and stores raw decoded text in cache."""
    try:
        content = file.file.read()
        return controller.upload_document(file.filename, content)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Upload parse failed: {str(e)}")


@router.post("/analyze")
def analyze_documents(req: ProcessRequest) -> Any:
    """Initiates synchronous or background async processing pipelines."""
    try:
        return controller.analyze(
            workspace_id=req.workspace_id,
            document_ids=req.document_ids,
            user_id=req.user_id,
            options=req.options
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")


@router.post("/process")
def process_documents_alias(req: ProcessRequest) -> Any:
    """Alias for backward compatibility with IDP reasoning engine."""
    return analyze_documents(req)


@router.post("/query", response_model=QueryResponse)
def query_documents(req: QueryRequest) -> Any:
    """Performs sliding-window citation-aware query mapping across documents."""
    try:
        return controller.query(
            workspace_id=req.workspace_id,
            document_ids=req.document_ids,
            query=req.query,
            options=req.options
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query resolution failed: {str(e)}")


@router.post("/compare")
def compare_documents(base_id: str = Query(...), target_id: str = Query(...)) -> Any:
    """Computes differences and keyword overlaps between two reports."""
    try:
        return controller.compare(base_id, target_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reports comparison failed: {str(e)}")


@router.get("/report/{report_id}", response_model=DocumentKnowledgeReport)
def get_report(report_id: str) -> Any:
    """Retrieves document knowledge report from cache or DB storage."""
    report = controller.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Document report '{report_id}' not found.")
    return report


@router.get("/history")
def get_history(workspace_id: str = Query(..., description="Workspace filter scope")) -> Any:
    """Retrieves list of previous analysis reports."""
    try:
        reports = controller.get_history(workspace_id)
        return {"history": [r.model_dump() for r in reports]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"History fetch failed: {str(e)}")


@router.get("/status/{execution_id}")
def get_status(execution_id: str) -> Any:
    """Retrieves status and progress dictionary for background jobs."""
    job = controller.get_status(execution_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Background analysis execution ID '{execution_id}' not found.")
    return job


@router.post("/index/search", response_model=List[str])
def search_index(req: SearchIndexRequest) -> Any:
    """Queries the compiled semantic index for keyword matching chunks."""
    try:
        return controller.service.search_semantic_index(
            report_id=req.report_id,
            search_type=req.search_type,
            query=req.query
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Index search failed: {str(e)}")
