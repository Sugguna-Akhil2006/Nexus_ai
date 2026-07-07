"""FastAPI router for the Platform Certification Suite."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.certification.certification_manager import CertificationManager
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/certification", tags=["Platform Certification"])

_manager = CertificationManager()


@router.post("/run", summary="Execute a full platform certification run")
def run_certification() -> Any:
    """Triggers the complete certification pipeline across all subsystems.

    Returns the scored run with domain reports, certification level,
    and recommended improvements.
    """
    run = _manager.run()
    return ProductResponse.ok(data=run)


@router.get("/status", summary="Get latest certification run status")
def get_status() -> Any:
    """Returns the most recent certification run summary."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No certification runs found. POST /certification/run first.")
    return ProductResponse.ok(
        data={
            "run_id": run.run_id,
            "overall_score": run.overall_score,
            "certification_level": run.certification_level.value,
            "total_checks": run.total_checks,
            "total_passed": run.total_passed,
            "total_failed": run.total_failed,
            "total_warnings": run.total_warnings,
            "completed_at": run.completed_at,
        }
    )


@router.get("/report", summary="Get latest certification report in chosen format")
def get_report(format: str = Query("json", description="Output format: json | markdown | html")) -> Any:
    """Returns the latest certification report in the requested format."""
    run = _manager.get_latest()
    if not run:
        raise HTTPException(status_code=404, detail="No certification runs found. POST /certification/run first.")

    fmt = format.lower()
    if fmt == "markdown":
        content = _manager.generate_markdown_report(run)
        return ProductResponse.ok(data={"format": "markdown", "content": content})
    elif fmt == "html":
        content = _manager.generate_html_report(run)
        return ProductResponse.ok(data={"format": "html", "content": content})
    else:
        content = _manager.generate_json_report(run)
        return ProductResponse.ok(data={"format": "json", "content": content})


@router.get("/history", summary="List all past certification runs")
def get_history() -> Any:
    """Returns summary records of all past certification runs."""
    runs = _manager.get_history()
    summaries = [
        {
            "run_id": r.run_id,
            "overall_score": r.overall_score,
            "certification_level": r.certification_level.value,
            "completed_at": r.completed_at,
        }
        for r in runs
    ]
    return ProductResponse.ok(data=summaries)
