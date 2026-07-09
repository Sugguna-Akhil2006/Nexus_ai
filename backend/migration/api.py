"""FastAPI router exposing migration check, trigger, and status routes."""

from __future__ import annotations

from typing import Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.migration.migration_manager import MigrationManager
from backend.migration.migration_report import MigrationReport
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/migration", tags=["Compatibility & Migration"])

_manager = MigrationManager()


class MigrationPayload(BaseModel):
    """Payload to trigger a platform migration run."""

    from_version: str
    to_version: str
    config: dict = {}
    plugins: List[dict] = []
    workflows: List[dict] = []


@router.get("/check", summary="Run compatibility check between versions")
def check_compatibility(
    from_version: str = Query(..., description="Installed version"),
    to_version: str = Query(..., description="Target upgrade version"),
) -> Any:
    """Evaluates version compatibility and scans public surfaces for breaking API / schema changes."""
    report = _manager.check_compatibility(from_version, to_version)
    return ProductResponse.ok(data=report)


@router.post("/run", summary="Execute migration plan with automatic rollback")
def run_migration(payload: MigrationPayload) -> Any:
    """Runs database schemas, configurations, plugins, and workflows upgrades."""
    run, migrated_cfg = _manager.run(
        from_version=payload.from_version,
        to_version=payload.to_version,
        config=payload.config,
        plugins=payload.plugins,
        workflows=payload.workflows,
    )
    return ProductResponse.ok(data={"run": run, "config": migrated_cfg})


@router.get("/status", summary="Get status of latest migration run")
def get_status() -> Any:
    """Returns summary fields of the latest migration run."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No migrations found. POST /migration/run first.")
    return ProductResponse.ok(
        data={
            "run_id": run.run_id,
            "from_version": run.from_version,
            "to_version": run.to_version,
            "status": run.status.value,
            "duration_ms": run.duration_ms,
            "completed_at": run.completed_at,
        }
    )


@router.get("/history", summary="Get migration history logs")
def get_history() -> Any:
    """Returns all past migration runs."""
    history = _manager.get_history()
    return ProductResponse.ok(data=history)


@router.get("/report", summary="Get migration report in chosen format")
def get_report(format: str = Query("markdown", description="markdown | json | html")) -> Any:
    """Generates the latest migration report in Markdown, JSON, or HTML."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No migration runs found.")

    fmt = format.lower()
    if fmt == "json":
        content = MigrationReport.to_json(run)
    elif fmt == "html":
        content = MigrationReport.to_html(run)
    else:
        content = MigrationReport.to_markdown(run)

    return ProductResponse.ok(data={"format": format, "content": content})
