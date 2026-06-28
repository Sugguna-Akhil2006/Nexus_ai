"""FastAPI Routers for Resume Intelligence Platform.

Exposes REST APIs for uploading, analyzing, comparing, matching, and exporting resumes.
"""

from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from backend.services.resume_service import ResumeOrchestrationService
from backend.tools.tool import ToolRegistry, ToolRequest

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

# =====================================================================
# Request / Response Schemas
# =====================================================================

class AnalyzeRequest(BaseModel):
    document_id: str
    workspace_id: str
    user_id: str = "admin"


class CompareRequest(BaseModel):
    document_ids: List[str]
    workspace_id: str
    jd: Optional[str] = None
    user_id: str = "admin"


class MatchRequest(BaseModel):
    document_id: str
    jd: str
    workspace_id: str
    user_id: str = "admin"


class ExportRequest(BaseModel):
    document_id: str
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
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {e}")


@router.post("/analyze")
def analyze_resume(req: AnalyzeRequest):
    """Performs structured metrics extraction and ATS analysis on an indexed resume."""
    service = ResumeOrchestrationService()
    try:
        report = service.analyze_resume(req.document_id, req.workspace_id, req.user_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


@router.post("/compare")
def compare_resumes(req: CompareRequest):
    """Runs a side-by-side comparison across multiple resumes."""
    service = ResumeOrchestrationService()
    tool_registry = ToolRegistry()
    
    # Retrieve raw texts of target documents
    resumes_list = []
    for doc_id in req.document_ids:
        text = service.get_resume_text(doc_id)
        resumes_list.append({"candidate_id": doc_id, "text": text})

    try:
        compare_tool = tool_registry.get_tool("resume_comparison")
        tool_res = compare_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="resume_comparison",
            workspace_id=req.workspace_id,
            user_id=req.user_id,
            arguments={"resumes": resumes_list, "jd": req.jd or ""}
        ))
        if not tool_res.success:
            raise HTTPException(status_code=500, detail=f"Comparison tool failed: {tool_res.output}")
        return tool_res.output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {e}")


@router.post("/match")
def match_resume(req: MatchRequest):
    """Matches a resume against a target job description."""
    service = ResumeOrchestrationService()
    try:
        match_data = service.match_resume_to_jd(req.document_id, req.jd, req.workspace_id, req.user_id)
        return match_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching failed: {e}")


@router.post("/export")
def export_report(req: ExportRequest):
    """Runs full analysis and generates a downloadable PDF Markdown representation."""
    service = ResumeOrchestrationService()
    tool_registry = ToolRegistry()
    
    try:
        # 1. Compile analysis report
        report = service.analyze_resume(req.document_id, req.workspace_id, req.user_id)
        
        # 2. Feed it to the PDF report generator tool
        pdf_tool = tool_registry.get_tool("pdf_generator")
        tool_res = pdf_tool.execute(ToolRequest(
            request_id=str(uuid.uuid4()),
            tool_id="pdf_generator",
            workspace_id=req.workspace_id,
            user_id=req.user_id,
            arguments={"report_data": report}
        ))
        if not tool_res.success:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {tool_res.output}")
        return {"document_id": req.document_id, "report_export": tool_res.output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
