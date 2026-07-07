"""FastAPI router exposing usage checks, trigger records, and stats reports."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.analytics.analytics_manager import AnalyticsManager
from backend.analytics.models import MetricType
from backend.product.serialization import ProductResponse

router = APIRouter(prefix="/analytics", tags=["Usage Analytics"])

_manager = AnalyticsManager()


class RecordPayload(BaseModel):
    """Payload to record an operational telemetry metric."""

    metric_type: MetricType
    name: str
    value: float
    context: dict = {}


@router.post("/record", summary="Record a telemetry metric entry")
def record_metric(payload: RecordPayload) -> Any:
    """Manually records a telemetry metric entry to the analytics dataset."""
    record = _manager.record(
        metric_type=payload.metric_type,
        name=payload.name,
        value=payload.value,
        context=payload.context,
    )
    return ProductResponse.ok(data=record)


@router.get("/summary", summary="Get aggregated usage analytics summary")
def get_summary() -> Any:
    """Returns the compiled aggregated dashboard report."""
    summary = _manager.aggregate()
    return ProductResponse.ok(data=summary)


@router.get("/report", summary="Get usage dashboard report in chosen format")
def get_report(format: str = Query("json", description="markdown | json | html")) -> Any:
    """Generates the latest compiled analytics report in chosen layout format."""
    content = _manager.generate_report(fmt=format.lower())
    return ProductResponse.ok(data={"format": format, "content": content})


@router.get("/metrics", summary="List raw metric records")
def list_metrics() -> Any:
    """Returns all collected raw telemetry metric events."""
    metrics = _manager.list_raw_metrics()
    return ProductResponse.ok(data=metrics)
