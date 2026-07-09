"""FastAPI APIRouter routing release readiness validation triggers and historical audits."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException

from backend.product.serialization import ProductResponse
from backend.release.models import ReleaseReadinessReport
from backend.release.release_manager import ReleaseManager

router = APIRouter(prefix="/release", tags=["Release Validation & Quality Gates"])

# Singleton manager
_manager = ReleaseManager()


@router.post("/validate", summary="Trigger a release validation run")
def run_validation() -> ProductResponse[Any]:
    """Executes all quality gates, audits system nodes, and creates a report."""
    report = _manager.run_validation()
    return ProductResponse.ok(data=report)


@router.get("/report", summary="Get the latest Release Readiness Report")
def get_report() -> ProductResponse[Optional[Dict[str, Any]]]:
    """Returns the most recently compiled release validation outcome from SQLite."""
    report = _manager.get_latest_report()
    if not report:
        # Run automatically if no report exists yet
        report_obj = _manager.run_validation()
        report = _manager.get_latest_report()
    return ProductResponse.ok(data=report)


@router.get("/history", summary="Get past release validation history logs")
def get_history() -> ProductResponse[List[Any]]:
    """Returns all historical quality gate reports recorded."""
    history = _manager.list_history()
    return ProductResponse.ok(data=history)
