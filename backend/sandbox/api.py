"""FastAPI APIRouter routing sandbox session creations, command executions, and file transfers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.sandbox.models import SandboxConfig
from backend.sandbox.sandbox_manager import SandboxManager

router = APIRouter(prefix="/sandbox", tags=["Secure Sandbox"])

# Singleton manager
_manager = SandboxManager()


class ExecuteCommandPayload(BaseModel):
    """Payload to trigger command execution."""

    command: str


@router.post("/sessions", summary="Create a new secure sandbox session")
def create_session(config: Optional[SandboxConfig] = None) -> Any:
    """Spawns an isolated folder workspace session for command runs."""
    session = _manager.create_session(config)
    return ProductResponse.ok(data=session)


@router.get("/sessions", summary="List active sandbox sessions")
def list_sessions() -> ProductResponse[List[Any]]:
    """Lists metadata for all active sandbox environments."""
    sessions = _manager.list_sessions()
    return ProductResponse.ok(data=sessions)


@router.post("/sessions/{session_id}/execute", summary="Execute command in session")
def execute_command(session_id: str, payload: ExecuteCommandPayload) -> Any:
    """Runs a whitelisted command inside the isolated session folder."""
    result = _manager.execute_in_session(session_id, payload.command)
    if result.exit_code == -5:
        raise HTTPException(status_code=404, detail=result.stderr)
    return ProductResponse.ok(data=result)


@router.post("/sessions/{session_id}/upload", summary="Upload file into session")
async def upload_file(session_id: str, filename: str = Query(...), file: UploadFile = File(...)) -> Any:
    """Saves a uploaded file inside the session working directory."""
    content = await file.read()
    success = _manager.upload_to_session(session_id, filename, content)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to upload file. Path may be unsafe or session closed.")
    return ProductResponse.ok(data={"filename": filename, "uploaded": True})


@router.get("/sessions/{session_id}/download", summary="Download artifact from session")
def download_artifact(session_id: str, filename: str = Query(...)) -> Any:
    """Reads a file out of the session working folder."""
    data = _manager.download_from_session(session_id, filename)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found or traversal blocked.")
    return Response(content=data, media_type="application/octet-stream")


@router.delete("/sessions/{session_id}", summary="Terminate secure sandbox session")
def terminate_session(session_id: str) -> Any:
    """Closes the session and cleans up temporary workspace files."""
    success = _manager.terminate_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return ProductResponse.ok(data={"session_id": session_id, "terminated": True})
