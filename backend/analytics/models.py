"""Pydantic models representing analytics events, aggregations, metrics, and trends."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetricType(str, Enum):
    """Supported metric categories."""

    WORKFLOW = "workflow"
    PROVIDER = "provider"
    INTELLIGENCE = "intelligence"
    RESOURCE = "resource"
    PRODUCT = "product"


class MetricRecord(BaseModel):
    """Individual data point captured by usage collector."""

    metric_id: str
    metric_type: MetricType
    name: str
    value: float
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=_utcnow)


class AggregateReport(BaseModel):
    """Combined summary of aggregated platform metrics."""

    start_time: str
    end_time: str
    workflow_metrics: Dict[str, Any] = Field(default_factory=dict)
    provider_metrics: Dict[str, Any] = Field(default_factory=dict)
    intelligence_metrics: Dict[str, Any] = Field(default_factory=dict)
    resource_metrics: Dict[str, Any] = Field(default_factory=dict)
    product_metrics: Dict[str, Any] = Field(default_factory=dict)
