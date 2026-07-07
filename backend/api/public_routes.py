"""Public REST API endpoints (/v1) for developer integration."""

import asyncio
from datetime import datetime
import json
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field

from backend.api.sqlite_mock import DBStorage
from backend.api.intelligence.gateway import IntelligenceGateway
from backend.api.intelligence.requests import GatewayExecutionRequest
from backend.intelligence.professional.professional_agent import ProfessionalAgent
from backend.intelligence.professional.models import ProfessionalAnalysisRequest
from backend.workflow.automation_engine import WorkflowExecutor

# Initialize router
router = APIRouter(prefix="/v1", tags=["Public API"])

from backend.registry.registry_api import router as registry_router
router.include_router(registry_router)


# Database initialization for job tracking
db_storage = DBStorage()

def init_public_db() -> None:
    conn = db_storage._get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS public_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress REAL NOT NULL,
            module TEXT NOT NULL,
            result TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            workspace_id TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS public_history (
            entry_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL,
            module TEXT NOT NULL,
            status TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            execution_time REAL NOT NULL
        )
        """)
        conn.commit()
    finally:
        conn.close()

init_public_db()

# Pydantic Schemas for Requests
class ResumeAnalyzeAPIRequest(BaseModel):
    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = []
    metadata: Dict[str, Any] = {}
    resume_text: str = ""
    document_id: str = ""


class GitHubAnalyzeAPIRequest(BaseModel):
    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = []
    metadata: Dict[str, Any] = {}
    repository_url: str = ""
    username: str = ""


class DocumentAnalyzeAPIRequest(BaseModel):
    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = []
    metadata: Dict[str, Any] = {}
    query: str = ""
    document_text: str = ""


class ProfessionalAnalyzeAPIRequest(BaseModel):
    workspace_id: str
    user_id: Optional[str] = None
    document_ids: List[str] = []
    metadata: Dict[str, Any] = {}
    resume_text: str = ""
    github_username: str = ""
    target_role: str = ""
    job_description: str = ""


class WorkflowRunAPIRequest(BaseModel):
    workflow_id: str
    workspace_id: str
    variables: Dict[str, Any] = {}
    user_id: Optional[str] = None


# Authentication Dependency
def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    authorization: Optional[str] = Header(None)
) -> str:
    """Simple API Key validation for public endpoints."""
    # Allow either X-API-Key or Bearer Token
    token = x_api_key
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing."
        )
    # For simulation/mock purposes, any non-empty key is accepted, but let's enforce a standard check
    if token == "invalid_key":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key or Bearer Token."
        )
    return token


# Helper to store and update jobs
def create_job(job_id: str, module: str, workspace_id: str) -> None:
    conn = db_storage._get_connection()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "INSERT INTO public_jobs (job_id, status, progress, module, created_at, updated_at, workspace_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, "pending", 0.0, module, now, now, workspace_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_job(job_id: str, status_str: str, progress: float, result: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
    conn = db_storage._get_connection()
    try:
        now = datetime.utcnow().isoformat()
        res_str = json.dumps(result) if result else None
        conn.execute(
            "UPDATE public_jobs SET status = ?, progress = ?, result = ?, error = ?, updated_at = ? WHERE job_id = ?",
            (status_str, progress, res_str, error, now, job_id)
        )
        conn.commit()
    finally:
        conn.close()


def log_history(job_id: str, module: str, status_str: str, workspace_id: str, created_at: str, elapsed: float) -> None:
    conn = db_storage._get_connection()
    try:
        entry_id = f"hist-{uuid.uuid4().hex[:8]}"
        conn.execute(
            "INSERT INTO public_history (entry_id, job_id, module, status, workspace_id, created_at, execution_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (entry_id, job_id, module, status_str, workspace_id, created_at, elapsed)
        )
        conn.commit()
    finally:
        conn.close()


# Background execution runners
def run_resume_analysis(job_id: str, req: ResumeAnalyzeAPIRequest, created_at: str) -> None:
    start_time = time.perf_counter()
    update_job(job_id, "running", 20.0)
    try:
        gateway = IntelligenceGateway()
        gw_req = GatewayExecutionRequest(
            workspace_id=req.workspace_id,
            user_id=req.user_id or "admin",
            capability="RESUME_PARSING",
            document_ids=req.document_ids or ([req.document_id] if req.document_id else []),
            metadata={
                "resume": req.resume_text,
                "filename": "resume.txt",
                **req.metadata
            }
        )
        update_job(job_id, "running", 50.0)
        res = gateway.route_and_execute(gw_req)
        
        status_str = "completed" if res.status == "completed" else "failed"
        err = "Gateway execution returned failed status" if status_str == "failed" else None
        
        # Format the result matching SDK AnalysisResponse expectations
        result_data = {
            "job_id": job_id,
            "status": status_str,
            "module": res.module,
            "execution_time": res.execution_time,
            "data": res.data,
            "warnings": res.warnings,
            "errors": res.errors
        }
        
        update_job(job_id, status_str, 100.0, result=result_data, error=err)
        log_history(job_id, "ResumeIntelligence", status_str, req.workspace_id, created_at, time.perf_counter() - start_time)
    except Exception as e:
        update_job(job_id, "failed", 100.0, error=str(e))
        log_history(job_id, "ResumeIntelligence", "failed", req.workspace_id, created_at, time.perf_counter() - start_time)


def run_github_analysis(job_id: str, req: GitHubAnalyzeAPIRequest, created_at: str) -> None:
    start_time = time.perf_counter()
    update_job(job_id, "running", 20.0)
    try:
        gateway = IntelligenceGateway()
        gw_req = GatewayExecutionRequest(
            workspace_id=req.workspace_id,
            user_id=req.user_id or "admin",
            capability="GITHUB_INTELLIGENCE",
            document_ids=req.document_ids,
            metadata={
                "repository_url": req.repository_url,
                "username": req.username,
                **req.metadata
            }
        )
        update_job(job_id, "running", 50.0)
        res = gateway.route_and_execute(gw_req)
        
        status_str = "completed" if res.status == "completed" else "failed"
        err = "Gateway execution returned failed status" if status_str == "failed" else None
        
        result_data = {
            "job_id": job_id,
            "status": status_str,
            "module": res.module,
            "execution_time": res.execution_time,
            "data": res.data,
            "warnings": res.warnings,
            "errors": res.errors
        }
        
        update_job(job_id, status_str, 100.0, result=result_data, error=err)
        log_history(job_id, "GitHubIntelligence", status_str, req.workspace_id, created_at, time.perf_counter() - start_time)
    except Exception as e:
        update_job(job_id, "failed", 100.0, error=str(e))
        log_history(job_id, "GitHubIntelligence", "failed", req.workspace_id, created_at, time.perf_counter() - start_time)


def run_document_analysis(job_id: str, req: DocumentAnalyzeAPIRequest, created_at: str) -> None:
    start_time = time.perf_counter()
    update_job(job_id, "running", 20.0)
    try:
        gateway = IntelligenceGateway()
        gw_req = GatewayExecutionRequest(
            workspace_id=req.workspace_id,
            user_id=req.user_id or "admin",
            capability="DOCUMENT_INTELLIGENCE",
            document_ids=req.document_ids,
            metadata={
                "query": req.query,
                "document_text": req.document_text,
                **req.metadata
            }
        )
        update_job(job_id, "running", 50.0)
        res = gateway.route_and_execute(gw_req)
        
        status_str = "completed" if res.status == "completed" else "failed"
        err = "Gateway execution returned failed status" if status_str == "failed" else None
        
        result_data = {
            "job_id": job_id,
            "status": status_str,
            "module": res.module,
            "execution_time": res.execution_time,
            "data": res.data,
            "warnings": res.warnings,
            "errors": res.errors
        }
        
        update_job(job_id, status_str, 100.0, result=result_data, error=err)
        log_history(job_id, "DocumentIntelligence", status_str, req.workspace_id, created_at, time.perf_counter() - start_time)
    except Exception as e:
        update_job(job_id, "failed", 100.0, error=str(e))
        log_history(job_id, "DocumentIntelligence", "failed", req.workspace_id, created_at, time.perf_counter() - start_time)


def run_professional_analysis(job_id: str, req: ProfessionalAnalyzeAPIRequest, created_at: str) -> None:
    start_time = time.perf_counter()
    update_job(job_id, "running", 20.0)
    try:
        agent = ProfessionalAgent()
        prof_req = ProfessionalAnalysisRequest(
            workspace_id=req.workspace_id,
            user_id=req.user_id or "admin",
            resume_text=req.resume_text,
            github_username=req.github_username,
            target_role=req.target_role,
            job_description=req.job_description,
            metadata=req.metadata
        )
        update_job(job_id, "running", 50.0)
        res = agent.analyze(prof_req)
        
        result_data = {
            "job_id": job_id,
            "status": "completed",
            "module": "ProfessionalIntelligence",
            "execution_time": time.perf_counter() - start_time,
            "data": res.model_dump() if hasattr(res, "model_dump") else str(res),
            "warnings": [],
            "errors": {}
        }
        
        update_job(job_id, "completed", 100.0, result=result_data)
        log_history(job_id, "ProfessionalIntelligence", "completed", req.workspace_id, created_at, time.perf_counter() - start_time)
    except Exception as e:
        update_job(job_id, "failed", 100.0, error=str(e))
        log_history(job_id, "ProfessionalIntelligence", "failed", req.workspace_id, created_at, time.perf_counter() - start_time)


def run_workflow_execution(job_id: str, req: WorkflowRunAPIRequest, created_at: str) -> None:
    start_time = time.perf_counter()
    update_job(job_id, "running", 20.0)
    try:
        executor = WorkflowExecutor()
        update_job(job_id, "running", 50.0)
        instance_id = executor.execute(req.workflow_id, req.variables)
        
        # Check workflow status (wait a bit or just return the instance details)
        result_data = {
            "job_id": job_id,
            "status": "completed",
            "module": "WorkflowEngine",
            "execution_time": time.perf_counter() - start_time,
            "data": {
                "instance_id": instance_id,
                "workflow_id": req.workflow_id
            },
            "warnings": [],
            "errors": {}
        }
        
        update_job(job_id, "completed", 100.0, result=result_data)
        log_history(job_id, "WorkflowEngine", "completed", req.workspace_id, created_at, time.perf_counter() - start_time)
    except Exception as e:
        update_job(job_id, "failed", 100.0, error=str(e))
        log_history(job_id, "WorkflowEngine", "failed", req.workspace_id, created_at, time.perf_counter() - start_time)


# Endpoint handlers
@router.post("/resume/analyze")
def analyze_resume(
    req: ResumeAnalyzeAPIRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat()
    create_job(job_id, "ResumeIntelligence", req.workspace_id)
    background_tasks.add_task(run_resume_analysis, job_id, req, created_at)
    return {"job_id": job_id, "status": "pending"}


@router.post("/github/analyze")
def analyze_github(
    req: GitHubAnalyzeAPIRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat()
    create_job(job_id, "GitHubIntelligence", req.workspace_id)
    background_tasks.add_task(run_github_analysis, job_id, req, created_at)
    return {"job_id": job_id, "status": "pending"}


@router.post("/document/analyze")
def analyze_document(
    req: DocumentAnalyzeAPIRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat()
    create_job(job_id, "DocumentIntelligence", req.workspace_id)
    background_tasks.add_task(run_document_analysis, job_id, req, created_at)
    return {"job_id": job_id, "status": "pending"}


@router.post("/professional/analyze")
def analyze_professional(
    req: ProfessionalAnalyzeAPIRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat()
    create_job(job_id, "ProfessionalIntelligence", req.workspace_id)
    background_tasks.add_task(run_professional_analysis, job_id, req, created_at)
    return {"job_id": job_id, "status": "pending"}


@router.post("/workflows/run")
def run_workflow(
    req: WorkflowRunAPIRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    created_at = datetime.utcnow().isoformat()
    create_job(job_id, "WorkflowEngine", req.workspace_id)
    background_tasks.add_task(run_workflow_execution, job_id, req, created_at)
    return {"job_id": job_id, "status": "pending"}


@router.get("/jobs/{id}")
def get_job_status(id: str, api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    conn = db_storage._get_connection()
    try:
        row = conn.execute("SELECT * FROM public_jobs WHERE job_id = ?", (id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Job not found.")
        
        result_dict = None
        if row["result"]:
            try:
                result_dict = json.loads(row["result"])
            except Exception:
                pass
                
        return {
            "job_id": row["job_id"],
            "status": row["status"],
            "progress": row["progress"],
            "module": row["module"],
            "result": result_dict,
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }
    finally:
        conn.close()


@router.get("/history")
def get_history(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    conn = db_storage._get_connection()
    try:
        rows = conn.execute("SELECT * FROM public_history ORDER BY created_at DESC").fetchall()
        history_list = []
        for r in rows:
            history_list.append({
                "entry_id": r["entry_id"],
                "job_id": r["job_id"],
                "module": r["module"],
                "status": r["status"],
                "workspace_id": r["workspace_id"],
                "created_at": r["created_at"],
                "execution_time": r["execution_time"]
            })
        return {"history": history_list}
    finally:
        conn.close()


# Workspace Management endpoints
class WorkspaceCreateAPIRequest(BaseModel):
    name: str


@router.post("/workspaces")
def create_public_workspace(
    req: WorkspaceCreateAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.agents.workspace import WorkspaceAgent
    from backend.runtime.task import Task
    agent = WorkspaceAgent()
    agent.initialize()
    
    ws_id = f"ws-{uuid.uuid4().hex[:8]}"
    task = Task(
        description="Create workspace",
        metadata={
            "action": "create_workspace",
            "workspace_id": ws_id,
            "name": req.name,
            "owner_id": "admin"
        }
    )
    res = agent.execute(task)
    return {"status": "success", "workspace": {
        "workspace_id": ws_id,
        "name": req.name,
        "status": "active"
    }}


@router.get("/workspaces")
def list_public_workspaces(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    rows = db_storage.list_workspaces("admin")
    return {"workspaces": rows}


# File Upload endpoints
from fastapi import UploadFile, File

def _extract_text(contents: bytes, filename: str) -> str:
    name_lower = filename.lower()
    try:
        if name_lower.endswith(".docx"):
            from docx import Document as DocxDocument
            doc = DocxDocument(io.BytesIO(contents))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        elif name_lower.endswith(".pdf"):
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(contents))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages)
        else:
            return contents.decode("utf-8", errors="ignore")
    except Exception:
        return contents.decode("utf-8", errors="ignore")


@router.post("/files/upload")
async def upload_public_file(
    workspace_id: str,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    contents = await file.read()
    text = _extract_text(contents, file.filename or "")
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from file.")
        
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    import hashlib
    checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    
    db_storage.create_document(doc_id, workspace_id, file.filename or "file", checksum)
    
    from backend.agents.embedding import EmbeddingAgent
    from backend.runtime.task import Task
    agent = EmbeddingAgent()
    agent.initialize()
    
    task_embed = Task(
        description="Index document content",
        metadata={
            "action": "embed",
            "workspace_id": workspace_id,
            "document_id": doc_id,
            "text": text,
            "filename": file.filename or "file",
            "checksum": checksum,
            "collection": "default_wiki"
        }
    )
    agent.execute(task_embed)
    db_storage.update_document_status(doc_id, "indexed")
    
    return {"status": "success", "document_id": doc_id, "chars_extracted": len(text)}


@router.get("/files")
def list_public_files(
    workspace_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    rows = db_storage.list_documents(workspace_id)
    return {"files": rows}


# Governance Schemas & Endpoints
class GovernanceValidateAPIRequest(BaseModel):
    context: Dict[str, Any]
    payload: Dict[str, Any]


class GovernanceRiskAPIRequest(BaseModel):
    context: Dict[str, Any]
    payload: Dict[str, Any]


@router.post("/governance/validate")
def validate_governance_policy(
    req: GovernanceValidateAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.governance.governance_engine import GovernanceEngine
    engine = GovernanceEngine()
    decision = engine.validate_execution(req.context, req.payload)
    
    # Map decision object to dict manually to ensure pydantic compatibility
    return {
        "is_approved": decision.is_approved,
        "risk_level": decision.risk_level.value,
        "approval_type": decision.approval_type.value,
        "decision_reasons": decision.decision_reasons,
        "security_check": {
            "has_prompt_injection": decision.security_check.has_prompt_injection if decision.security_check else False,
            "detected_pii": decision.security_check.detected_pii if decision.security_check else [],
            "has_unsafe_tools": decision.security_check.has_unsafe_tools if decision.security_check else False,
            "is_malicious_file": decision.security_check.is_malicious_file if decision.security_check else False,
            "warnings": decision.security_check.warnings if decision.security_check else []
        } if decision.security_check else None,
        "risk_assessment": {
            "risk_level": decision.risk_assessment.risk_level.value if decision.risk_assessment else "low",
            "score": decision.risk_assessment.score if decision.risk_assessment else 0.1,
            "explanation": decision.risk_assessment.explanation if decision.risk_assessment else ""
        } if decision.risk_assessment else None
    }


@router.post("/governance/risk")
def assess_governance_risk(
    req: GovernanceRiskAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.governance.governance_engine import GovernanceEngine
    engine = GovernanceEngine()
    assessment = engine.assess_payload_risk(req.context, req.payload)
    return {
        "risk_level": assessment.risk_level.value,
        "score": assessment.score,
        "explanation": assessment.explanation
    }


@router.get("/governance/audit")
def get_governance_audit(
    workspace_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.governance.governance_engine import GovernanceEngine
    engine = GovernanceEngine()
    logs = engine.get_audit_history(workspace_id)
    serialized_logs = []
    for l in logs:
        serialized_logs.append({
            "record_id": l.record_id,
            "timestamp": l.timestamp,
            "user_id": l.user_id,
            "workspace_id": l.workspace_id,
            "module_used": l.module_used,
            "model_used": l.model_used,
            "provider_used": l.provider_used,
            "tokens_consumed": l.tokens_consumed,
            "cost_estimated": l.cost_estimated,
            "latency_ms": l.latency_ms,
            "status": l.status,
            "policy_violations": l.policy_violations,
            "security_alerts": l.security_alerts,
            "risk_level": l.risk_level
        })
    return {"audit_trail": serialized_logs}


@router.get("/governance/compliance")
def get_governance_compliance(
    workspace_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.governance.governance_report import GovernanceReportGenerator
    generator = GovernanceReportGenerator()
    report = generator.generate_report(workspace_id)
    return report["compliance_status"]


@router.get("/governance/dashboard")
def get_governance_dashboard(
    workspace_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.governance.governance_report import GovernanceReportGenerator
    generator = GovernanceReportGenerator()
    report = generator.generate_report(workspace_id)
    return report


# Studio Schemas & Endpoints
class ProjectGenerateAPIRequest(BaseModel):
    component_type: str
    name: str
    output_dir: str


@router.get("/studio/workspace/info")
def get_studio_workspace_info(
    workspace_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    overview = studio.get_workspace_overview(workspace_id)
    return overview


@router.get("/studio/inspect/agent/{agent_id}")
def inspect_studio_agent(
    agent_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    inspection = studio.agent_ins.inspect_agent(agent_id)
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found.")
    
    return {
        "agent_id": inspection.agent_id,
        "name": inspection.name,
        "capabilities": inspection.capabilities,
        "health_status": inspection.health_status,
        "current_tasks": inspection.current_tasks,
        "execution_history": inspection.execution_history,
        "dependencies": inspection.dependencies
    }


@router.get("/studio/inspect/memory/{workspace_id}")
def inspect_studio_memory(
    workspace_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    mem = studio.memory_ins.get_memory_snapshot(workspace_id)
    return {
        "workspace_id": mem.workspace_id,
        "short_term": mem.short_term,
        "long_term": mem.long_term,
        "knowledge_profile": mem.knowledge_profile,
        "memory_usage_bytes": mem.memory_usage_bytes
    }


@router.post("/studio/project/generate")
def generate_studio_project(
    req: ProjectGenerateAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    try:
        path = studio.generator.generate_component(req.component_type, req.name, req.output_dir)
        return {"status": "success", "generated_path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/studio/dashboard/health")
def get_studio_health(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    return studio.get_studio_health_status()


@router.get("/studio/export/config")
def export_studio_config(
    format: str = "json",
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.studio.studio_service import StudioService
    studio = StudioService()
    try:
        content = studio.config_mgr.export_as(format)
        return {"status": "success", "format": format, "content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# MCP Schemas & Endpoints
class MCPToolExecuteAPIRequest(BaseModel):
    server_name: str
    tool_name: str
    params: Dict[str, Any] = {}


@router.get("/mcp/servers")
def list_mcp_servers(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.mcp.registry import MCPRegistry
    reg = MCPRegistry()
    servers = reg.list_servers()
    return {
        "servers": [
            {
                "server_id": s.server_id,
                "name": s.name,
                "version": s.version,
                "status": s.status
            } for s in servers
        ]
    }


@router.get("/mcp/tools")
def list_mcp_tools(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.mcp.tool_adapter import MCPToolAdapter
    adapter = MCPToolAdapter()
    tools = adapter.get_sdk_tools()
    return {
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "inputSchema": t.inputSchema
            } for t in tools.values()
        ]
    }


@router.get("/mcp/resources")
def list_mcp_resources(
    workspace_id: str = "default",
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.mcp.resource_adapter import MCPResourceAdapter
    adapter = MCPResourceAdapter()
    resources = adapter.get_sdk_resources(workspace_id)
    return {
        "resources": [
            {
                "uri": r.uri,
                "name": r.name,
                "mimeType": r.mimeType,
                "description": r.description
            } for r in resources
        ]
    }


@router.post("/mcp/tool/execute")
def execute_mcp_tool(
    req: MCPToolExecuteAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.mcp.client import MCPClient
    client = MCPClient()
    try:
        # Establish trusted connection
        client.connect_server(req.server_name)
        res = client.execute_tool(req.server_name, req.tool_name, req.params)
        return {"status": "success", "result": res}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Platform Operations Center Endpoints
@router.get("/platform/providers")
def list_platform_providers(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.platform.platform_manager import PlatformManager
    mgr = PlatformManager()
    providers = mgr.provider_mgr.list_providers()
    return {
        "providers": [
            {
                "provider_id": p.provider_id,
                "name": p.name,
                "is_active": p.is_active,
                "api_url": p.api_url,
                "health_status": p.health_status,
                "error_rate": p.error_rate
            } for p in providers
        ]
    }


@router.get("/platform/models")
def list_platform_models(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.platform.platform_manager import PlatformManager
    mgr = PlatformManager()
    models = mgr.model_mgr.list_models()
    return {
        "models": [
            {
                "model_id": m.model_id,
                "name": m.name,
                "provider_id": m.provider_id,
                "version": m.version,
                "capabilities": m.capabilities,
                "is_active": m.is_active,
                "is_default": m.is_default
            } for m in models
        ]
    }


@router.get("/platform/dashboard")
def get_platform_dashboard(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.platform.platform_manager import PlatformManager
    mgr = PlatformManager()
    return mgr.get_admin_dashboard_metrics()


# Universal Connector Framework Endpoints
class ConnectorConnectAPIRequest(BaseModel):
    connector_id: str
    workspace_id: str
    connector_type: str
    name: str
    auth_data: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


@router.post("/connectors/connect")
def connect_external_system(
    req: ConnectorConnectAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.connectors.connector_manager import ConnectorManager
    from backend.connectors.models import ConnectorConfig
    mgr = ConnectorManager()
    cfg = ConnectorConfig(
        connector_id=req.connector_id,
        workspace_id=req.workspace_id,
        connector_type=req.connector_type,
        name=req.name,
        auth_data=req.auth_data,
        metadata=req.metadata
    )
    try:
        mgr.configure_connector(cfg)
        return {"status": "success", "message": f"Connected to {req.connector_type} system successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connectors/disconnect")
def disconnect_external_system(
    connector_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.connectors.connector_manager import ConnectorManager
    mgr = ConnectorManager()
    try:
        mgr.delete_connector(connector_id)
        return {"status": "success", "message": "Connector deleted."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/connectors/sync")
def sync_connector_data(
    connector_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.connectors.connector_manager import ConnectorManager
    mgr = ConnectorManager()
    try:
        job = mgr.sync_connector(connector_id)
        return {
            "status": "success",
            "job_id": job.job_id if job else None,
            "sync_status": job.status if job else None,
            "records_processed": job.records_processed if job else 0
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/connectors/health")
def get_connector_health(
    connector_id: str,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.connectors.connector_manager import ConnectorManager
    mgr = ConnectorManager()
    config = mgr.get_connector(connector_id)
    if not config:
        raise HTTPException(status_code=404, detail="Connector config not found.")
    
    h = mgr.health_monitor.check_health(config)
    return {
        "status": h.status,
        "latency_ms": h.latency_ms,
        "last_check": h.last_check_timestamp.isoformat() if h.last_check_timestamp else None,
        "error_details": h.error_details
    }


# Intelligent Model Router Endpoints
class RouterRouteAPIRequest(BaseModel):
    task_type: str
    required_capabilities: List[str] = []
    min_context_length: int = 4096
    requires_streaming: bool = False
    policy_preference: str = "balanced"
    workspace_id: str = "default"


@router.post("/router/route")
def route_inference_request(
    req: RouterRouteAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.providers.router.model_router import ModelRouter
    from backend.providers.router.models import InferenceRequest
    router_engine = ModelRouter()
    r = InferenceRequest(
        task_type=req.task_type,
        required_capabilities=req.required_capabilities,
        min_context_length=req.min_context_length,
        requires_streaming=req.requires_streaming,
        policy_preference=req.policy_preference,
        workspace_id=req.workspace_id
    )
    try:
        recommendation = router_engine.route_request(r)
        return {
            "status": "success",
            "model_id": recommendation.model_id,
            "provider_id": recommendation.provider_id,
            "estimated_cost": recommendation.estimated_cost,
            "estimated_latency_ms": recommendation.estimated_latency_ms,
            "quality_rank": recommendation.quality_rank
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/router/metrics")
def get_routing_metrics(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.platform.platform_manager import PlatformManager
    mgr = PlatformManager()
    summary = mgr.analytics.get_metrics_summary()
    return {
        "total_requests": summary.total_requests,
        "total_cost": summary.total_cost,
        "average_latency_ms": summary.average_latency_ms,
        "error_count": summary.error_count
    }


# Unified Knowledge Fabric Endpoints
class FabricIngestAPIRequest(BaseModel):
    name: str
    category: str
    source_module: str
    source_ref: str
    confidence: float = 1.0
    relationships_tags: List[str] = []
    metadata: Dict[str, Any] = {}


@router.post("/fabric/ingest")
def ingest_fabric_fact(
    req: FabricIngestAPIRequest,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.knowledge_fabric.fabric_manager import FabricManager
    fabric = FabricManager()
    try:
        ent = fabric.ingest_new_fact(
            name=req.name,
            category=req.category,
            source_module=req.source_module,
            source_ref=req.source_ref,
            confidence=req.confidence,
            relationships_tags=req.relationships_tags,
            metadata=req.metadata
        )
        return {
            "status": "success",
            "entity_id": ent.entity_id,
            "canonical_name": ent.name,
            "category": ent.category
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fabric/entities")
def list_fabric_entities(
    query: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.knowledge_fabric.fabric_manager import FabricManager
    fabric = FabricManager()
    if query:
        entities = fabric.search_entities(query)
    else:
        entities = fabric.get_resolved_entities()
    return {
        "entities": [
            {
                "entity_id": e.entity_id,
                "name": e.name,
                "category": e.category,
                "metadata": e.metadata
            } for e in entities
        ]
    }


@router.get("/fabric/relationships")
def list_fabric_relationships(
    entity_id: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.knowledge_fabric.fabric_manager import FabricManager
    fabric = FabricManager()
    if entity_id:
        rels = fabric.query_engine.get_neighborhood(entity_id)
    else:
        rels = fabric.query_engine.list_relationships()
    return {
        "relationships": [
            {
                "relationship_id": r.relationship_id,
                "source_id": r.source_id,
                "target_id": r.target_id,
                "relation_type": r.relation_type,
                "confidence": r.confidence
            } for r in rels
        ]
    }


@router.post("/fabric/snapshot")
def create_fabric_snapshot(
    api_key: str = Depends(verify_api_key)
) -> Dict[str, Any]:
    from backend.knowledge_fabric.fabric_manager import FabricManager
    fabric = FabricManager()
    try:
        snap = fabric.create_state_snapshot()
        return {
            "status": "success",
            "snapshot_id": snap.snapshot_id,
            "timestamp": snap.timestamp.isoformat(),
            "entities_count": len(snap.entities),
            "relationships_count": len(snap.relationships)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Distributed Runtime Endpoints ─────────────────────────────────────────

# Singleton cluster instance (lazy-init, no background threads for API use)
_cluster_instance = None
_cluster_lock = threading.Lock()


def _get_cluster():
    """Returns the shared ClusterManager instance."""
    global _cluster_instance
    if _cluster_instance is None:
        with _cluster_lock:
            if _cluster_instance is None:
                from backend.distributed.cluster_manager import ClusterManager
                _cluster_instance = ClusterManager()
    return _cluster_instance


class WorkerRegisterRequest(BaseModel):
    address: str
    capabilities: List[str] = []
    node_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class WorkerHeartbeatRequest(BaseModel):
    node_id: str
    cpu_usage_percent: float = 0.0
    memory_used_mb: int = 0
    queue_size: int = 0


class TaskSubmitRequest(BaseModel):
    workflow_id: str
    payload: Dict[str, Any] = {}
    priority: int = 5
    required_capabilities: List[str] = []
    max_retries: int = 3
    timeout_seconds: float = 60.0


@router.post("/cluster/workers/register")
def register_cluster_worker(
    req: WorkerRegisterRequest,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Registers a new worker node with the distributed cluster."""
    cluster = _get_cluster()
    node = cluster.register_worker(
        address=req.address,
        capabilities=req.capabilities,
        node_id=req.node_id,
        metadata=req.metadata,
    )
    return {
        "status": "registered",
        "node_id": node.node_id,
        "address": node.address,
        "capabilities": node.capabilities,
    }


@router.post("/cluster/workers/heartbeat")
def worker_heartbeat(
    req: WorkerHeartbeatRequest,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Records a heartbeat from a registered worker node."""
    from backend.distributed.models import ResourceProfile
    cluster = _get_cluster()
    resources = ResourceProfile(
        cpu_usage_percent=req.cpu_usage_percent,
        memory_used_mb=req.memory_used_mb,
        queue_size=req.queue_size,
    )
    cluster.heartbeat(req.node_id, resources)
    return {"status": "ok", "node_id": req.node_id}


@router.delete("/cluster/workers/{node_id}")
def remove_cluster_worker(
    node_id: str,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Removes a worker node from the cluster."""
    cluster = _get_cluster()
    cluster.remove_worker(node_id)
    return {"status": "removed", "node_id": node_id}


@router.get("/cluster/health")
def get_cluster_health(
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Returns the current cluster health snapshot."""
    cluster = _get_cluster()
    snap = cluster.get_cluster_snapshot()
    return {
        "snapshot_id": snap.snapshot_id,
        "timestamp": snap.timestamp.isoformat(),
        "total_nodes": snap.total_nodes,
        "online_nodes": snap.online_nodes,
        "tasks_queued": snap.total_tasks_queued,
        "tasks_running": snap.total_tasks_running,
        "cluster_load": snap.cluster_load,
        "nodes": snap.nodes,
    }


@router.post("/cluster/tasks/submit")
def submit_cluster_task(
    req: TaskSubmitRequest,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Submits a task to the distributed execution queue."""
    cluster = _get_cluster()
    task_id = cluster.submit_task(
        workflow_id=req.workflow_id,
        payload=req.payload,
        priority=req.priority,
        required_capabilities=req.required_capabilities,
        max_retries=req.max_retries,
        timeout_seconds=req.timeout_seconds,
    )
    return {"status": "queued", "task_id": task_id, "workflow_id": req.workflow_id}


@router.get("/cluster/workflows/{workflow_id}/progress")
def get_workflow_progress(
    workflow_id: str,
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Returns task completion progress for a distributed workflow."""
    cluster = _get_cluster()
    return cluster.get_workflow_progress(workflow_id)


@router.get("/cluster/tasks/active")
def list_active_cluster_tasks(
    api_key: str = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Lists all currently executing tasks across the cluster."""
    cluster = _get_cluster()
    tasks = cluster.list_active_tasks()
    return {
        "active_tasks": [
            {
                "task_id": t.task_id,
                "workflow_id": t.workflow_id,
                "status": t.status.value,
                "assigned_node_id": t.assigned_node_id,
                "priority": t.priority,
            }
            for t in tasks
        ]
    }









