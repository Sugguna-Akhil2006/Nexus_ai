"""Pydantic data models for the AI Governance & Compliance Center."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ApprovalState(str, Enum):
    """Lifecycle/deployment approval state of a model."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


class ModelRecord(BaseModel):
    """Metadata block for registered LLMs."""

    model_id: str
    name: str
    version: str
    provider: str
    status: str = "active"  # "active" | "deprecated" | "retired"
    approval_state: ApprovalState = ApprovalState.PENDING
    registered_at: str = Field(default_factory=_utcnow)


class AuditTrailEntry(BaseModel):
    """Historical event captured for security audit trails."""

    audit_id: str
    timestamp: str = Field(default_factory=_utcnow)
    category: str  # "workflow" | "policy" | "provider" | "config" | "admin"
    actor: str
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)


class ComplianceCheckResult(BaseModel):
    """Structural report of compliance evaluations."""

    rule_name: str
    passed: bool
    details: str


class ComplianceStatusReport(BaseModel):
    """Aggregate compliance reports."""

    overall_passed: bool
    checked_at: str = Field(default_factory=_utcnow)
    results: List[ComplianceCheckResult] = Field(default_factory=list)


class RiskLevel(str, Enum):
    """Governance risk tiers."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskReport(BaseModel):
    """Risk calculation metrics and alerts."""

    risk_level: RiskLevel
    score: float  # 0.0 to 1.0
    alerts: List[str] = Field(default_factory=list)
    calculated_at: str = Field(default_factory=_utcnow)
