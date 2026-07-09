"""FastAPI router for the Disaster Recovery & Business Continuity API."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.recovery.models import (
    BackupType,
    CheckpointType,
    FailureScenario,
    RestoreRequest,
)
from backend.recovery.recovery_manager import RecoveryManager

router = APIRouter(prefix="/recovery", tags=["Disaster Recovery"])

_manager = RecoveryManager()


class CheckpointPayload(BaseModel):
    """Payload for saving a new checkpoint."""

    checkpoint_type: CheckpointType
    component_id: str
    state: dict = {}
    metadata: dict = {}


class BackupPayload(BaseModel):
    """Payload for triggering a backup."""

    backup_type: BackupType = BackupType.FULL


class RecoverPayload(BaseModel):
    """Payload for triggering a scenario recovery."""

    scenario: FailureScenario = FailureScenario.APPLICATION_RESTART


@router.post("/checkpoint", summary="Persist a component state checkpoint")
def save_checkpoint(payload: CheckpointPayload) -> Any:
    """Saves a component state checkpoint to the persistent store."""
    cp = _manager.save_checkpoint(
        checkpoint_type=payload.checkpoint_type,
        component_id=payload.component_id,
        state=payload.state,
        metadata=payload.metadata,
    )
    return ProductResponse.ok(data=cp)


@router.post("/backup", summary="Trigger a manual backup snapshot")
def trigger_backup(payload: BackupPayload) -> Any:
    """Creates a full, incremental, or metadata backup of all checkpoints."""
    record = _manager.backup(payload.backup_type)
    return ProductResponse.ok(data=record)


@router.post("/restore", summary="Restore from a checkpoint or backup")
def restore(request: RestoreRequest) -> Any:
    """Executes a restore operation from checkpoint ID, component, or type."""
    result = _manager.restore(request)
    if not result.get("success"):
        raise HTTPException(status_code=422, detail=result.get("detail", "Restore failed."))
    return ProductResponse.ok(data=result)


@router.post("/recover", summary="Run scenario-specific recovery pipeline")
def recover(payload: RecoverPayload) -> Any:
    """Executes the full recovery pipeline for the specified failure scenario."""
    run = _manager.recover(payload.scenario)
    return ProductResponse.ok(data=run)


@router.get("/status", summary="Get latest recovery run status")
def get_status() -> Any:
    """Returns a summary of the most recent recovery run."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No recovery runs found. POST /recovery/recover first.")
    return ProductResponse.ok(
        data={
            "run_id": run.run_id,
            "scenario": run.scenario.value,
            "status": run.status.value,
            "recovered_components": run.recovered_components,
            "failed_components": run.failed_components,
            "duration_ms": run.duration_ms,
            "integrity_verified": run.integrity_verified,
            "completed_at": run.completed_at,
        }
    )


@router.get("/history", summary="List all recovery run history")
def get_history() -> Any:
    """Returns all past recovery runs with summary fields."""
    runs = _manager.get_history()
    return ProductResponse.ok(
        data=[
            {
                "run_id": r.run_id,
                "scenario": r.scenario.value,
                "status": r.status.value,
                "duration_ms": r.duration_ms,
                "completed_at": r.completed_at,
            }
            for r in runs
        ]
    )


@router.get("/report", summary="Generate a recovery report in chosen format")
def get_report(format: str = Query("markdown", description="markdown | json | html")) -> Any:
    """Returns the latest recovery run report in the requested format."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No recovery runs found.")
    content = _manager.generate_report(fmt=format.lower())
    return ProductResponse.ok(data={"format": format, "content": content})


@router.get("/backups", summary="List all backup records")
def list_backups() -> Any:
    """Returns all backup snapshot records."""
    records = _manager.list_backups()
    return ProductResponse.ok(data=records)
