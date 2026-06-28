"""FastAPI Controllers for Resume Intelligence Platform.

Exposes REST APIs mapping to Prompt 37 exact endpoint paths.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.services.resume_service import ResumeOrchestrationService
from backend.api.sqlite_mock import DBStorage

# Define route prefix exactly as '/resume'
router = APIRouter(prefix="/resume", tags=["Resume"])

# =====================================================================
# Request / Response Schemas
# =====================================================================

class AnalyzeRequest(BaseModel):
    document_id: str
    workspace_id: str
    user_id: str = "admin"


class MatchRequest(BaseModel):
    document_id: str
    jd: str
    workspace_id: str
    user_id: str = "admin"


class CompareRequest(BaseModel):
    document_ids: List[str]
    workspace_id: str
    user_id: str = "admin"


# =====================================================================
# REST Endpoints
# =====================================================================

@router.post("/upload")
async def upload_resume(workspace_id: str, file: UploadFile = File(...)):
    """Uploads a resume file and indexes it in the vector store."""
    try:
        contents = await file.read()
        text = contents.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    service = ResumeOrchestrationService()
    try:
        doc_id = service.process_and_index_resume(file.filename, text, workspace_id)
        return {"status": "success", "document_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume upload: {e}")


@router.post("/analyze")
def analyze_resume(req: AnalyzeRequest):
    """Parses, stores metadata details in tables, scores, and updates ATS report history."""
    service = ResumeOrchestrationService()
    try:
        report = service.analyze_resume(req.document_id, req.workspace_id, req.user_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume analysis failed: {e}")


@router.post("/match")
def match_resume(req: MatchRequest):
    """Scores suitability matches and missing gap competencies metrics."""
    service = ResumeOrchestrationService()
    try:
        match_data = service.match_resume_to_jd(req.document_id, req.jd, req.workspace_id, req.user_id)
        return match_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching alignment failed: {e}")


@router.post("/compare")
def compare_resumes(req: CompareRequest):
    """Compares multiple versions/candidate documents side-by-side."""
    service = ResumeOrchestrationService()
    try:
        compare_data = service.compare_resumes(req.document_ids, req.workspace_id, req.user_id)
        return compare_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Version comparison failed: {e}")


@router.get("/report/{id}")
def get_resume_report(id: str, workspace_id: str = "default", user_id: str = "admin"):
    """Compiles and exports formats including Markdown, JSON, and PDF data models."""
    service = ResumeOrchestrationService()
    try:
        report_data = service.generate_report(id, workspace_id, user_id)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")
