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
from backend.intelligence.document.conversation import (
    ChatRequest,
    SearchRequest,
    SearchResponse,
    DocumentConversationResponse
)
from backend.intelligence.document.document_session import DocumentSessionManager

router = APIRouter(prefix="/document", tags=["document"])
controller = DocumentProductController()
session_manager = DocumentSessionManager()


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
        res = session_manager.chat_turn(
            workspace_id=req.workspace_id,
            query=req.query,
            document_ids=req.document_ids,
            options=req.options
        )
        return QueryResponse(
            query=req.query,
            answer=res.answer,
            citations=res.citations
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query resolution failed: {str(e)}")


@router.post("/chat", response_model=DocumentConversationResponse)
def chat_documents(req: ChatRequest) -> Any:
    """Continues multi-turn conversational reasoning context over files."""
    try:
        return session_manager.chat_turn(
            workspace_id=req.workspace_id,
            query=req.query,
            conversation_id=req.conversation_id,
            document_ids=req.document_ids,
            options=req.options
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


@router.post("/search", response_model=SearchResponse)
def search_documents(req: SearchRequest) -> Any:
    """Retrieves relevant document snippets via semantic/keyword retrieval."""
    try:
        chunks = session_manager.query_engine.search_chunks(
            workspace_id=req.workspace_id,
            query=req.query,
            document_ids=req.document_ids,
            search_mode=req.search_mode,
            limit=req.limit,
            options=req.options
        )
        
        # Log to workspace searches memory
        session_manager.memory.log_search(
            workspace_id=req.workspace_id,
            query=req.query,
            search_mode=req.search_mode,
            limit=req.limit,
            results_count=len(chunks)
        )
        
        results = []
        for c in chunks:
            results.append({
                "chunk_id": c.chunk_id,
                "text": c.text,
                "section": c.section
            })
        return SearchResponse(results=results)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search query failed: {str(e)}")


@router.get("/conversation/{conversation_id}")
def get_conversation(conversation_id: str) -> Any:
    """Retrieves history turns of a chat session."""
    try:
        messages = session_manager.memory.get_messages(conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": messages
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversation history: {str(e)}")


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
