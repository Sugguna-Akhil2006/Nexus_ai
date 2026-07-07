"""FastAPI APIRouter routing release candidate build triggers and history metrics."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.release_builder.models import ReleaseType
from backend.release_builder.release_builder import ReleaseCandidateBuilder

router = APIRouter(prefix="/release-builder", tags=["Release Candidate Builder"])

# Singleton builder
_builder = ReleaseCandidateBuilder()


class TriggerBuildPayload(BaseModel):
    """Payload to trigger a release candidate build."""

    current_version: str = "1.0.0-rc1"
    release_type: ReleaseType = ReleaseType.RC


@router.post("/build", summary="Trigger a release build")
def post_build(payload: TriggerBuildPayload) -> Any:
    """Runs quality gates, packages source, outputs manifest, and saves build logs."""
    record = _builder.build_release(
        current_version=payload.current_version,
        release_type=payload.release_type,
    )
    return ProductResponse.ok(data=record)


@router.get("/status", summary="Get status of latest release build")
def get_status() -> ProductResponse[Optional[Dict[str, Any]]]:
    """Returns the most recently recorded build log from SQLite history."""
    build = _builder.get_latest_build()
    if not build:
        # Run default build automatically if no history exists yet
        build_obj = _builder.build_release(current_version="1.0.0-rc1", release_type=ReleaseType.RC)
        build = _builder.get_latest_build()
    return ProductResponse.ok(data=build)


@router.get("/history", summary="Get release builder build history logs")
def get_history() -> ProductResponse[List[Any]]:
    """Returns all historical build candidate records registered."""
    history = _builder.list_history()
    return ProductResponse.ok(data=history)
