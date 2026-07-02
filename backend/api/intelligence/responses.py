"""Standardized response schemas returned by the API Gateway."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GatewayExecutionResponse(BaseModel):
    """Standardized API response mapping outcomes, timings, warnings, and payload data."""
    status: str = Field(..., description="Run status (completed, failed, cancelled, partial_success)")
    execution_id: str = Field(..., description="Unique runtime run run execution ID")
    module: str = Field(..., description="Triggered intelligence module name")
    execution_time: float = Field(0.0, description="Sum total execution time in seconds")
    data: Dict[str, Any] = Field(default_factory=dict, description="Consolidated payload findings data")
    warnings: List[str] = Field(default_factory=list, description="Non-breaking warning messages list")
    errors: Dict[str, str] = Field(default_factory=dict, description="Pipeline stage error messages dict")
    telemetry: Dict[str, Any] = Field(default_factory=dict, description="Metrics list mappings (like retry logs)")
