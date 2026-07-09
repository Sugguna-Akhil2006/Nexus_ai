"""Pydantic data models representing quality gates and release validation structures."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class GateStatus(str, Enum):
    """Execution status of an individual quality gate."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class QualityGateResult(BaseModel):
    """The outcome of evaluating a single operational quality rule."""

    gate_name: str
    description: str
    status: GateStatus = GateStatus.PASSED
    message: Optional[str] = None
    severity: str = "medium"  # "low" | "medium" | "high" | "critical"


class PerformanceAudit(BaseModel):
    """Timing and resource thresholds logged during testing."""

    startup_time_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    cpu_usage_pct: float = 0.0
    streaming_latency_ms: float = 0.0


class SecurityAudit(BaseModel):
    """Validation outcomes of gateway settings and masked properties."""

    auth_active: bool = True
    secrets_masked: bool = True
    rate_limiting_active: bool = True
    vulnerabilities_count: int = 0


class ReleaseReadinessReport(BaseModel):
    """Consolidated document detailing quality outcomes and release scoring."""

    report_id: str
    readiness_score: int = 0  # [0, 100]
    is_deployable: bool = False
    passed_gates: List[str] = Field(default_factory=list)
    failed_gates: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    recommended_fixes: List[str] = Field(default_factory=list)
    performance: PerformanceAudit = Field(default_factory=PerformanceAudit)
    security: SecurityAudit = Field(default_factory=SecurityAudit)
    created_at: str
