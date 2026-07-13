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


class ApprovalType(str, Enum):
    """Workflow routing types."""
    AUTO = "auto"
    MANUAL = "manual"


class SecurityCheckResult(BaseModel):
    """Security check results scans."""
    has_prompt_injection: bool = False
    detected_pii: List[str] = Field(default_factory=list)
    has_unsafe_tools: bool = False
    is_malicious_file: bool = False
    warnings: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Audit risk level outcome."""
    risk_level: RiskLevel
    score: float
    alerts: List[str] = Field(default_factory=list)


class ComplianceStatus(BaseModel):
    """GDPR/SOC2/ISO Compliance check status."""
    gdpr_compliant: bool = True
    soc2_compliant: bool = True
    iso_compliant: bool = True
    enterprise_compliant: bool = True
    non_compliant_reasons: List[str] = Field(default_factory=list)


class GovernanceDecision(BaseModel):
    """Decision block made by governance engine guard."""
    is_approved: bool
    risk_level: RiskLevel
    approval_type: ApprovalType
    decision_reasons: List[str] = Field(default_factory=list)
    security_check: SecurityCheckResult
    risk_assessment: RiskAssessment


class AuditRecord(BaseModel):
    """System audit logs tracking details."""
    record_id: str
    timestamp: str
    user_id: str
    workspace_id: str
    module_used: str
    model_used: str
    provider_used: str
    tokens_consumed: int
    cost_estimated: float
    latency_ms: float
    status: str
    policy_violations: List[str] = Field(default_factory=list)
    security_alerts: List[str] = Field(default_factory=list)
    risk_level: str


class PolicyRule(BaseModel):
    """Governance policy validation rules."""
    policy_id: str
    name: str
    workspace_id: str
    allowed_modules: List[str] = Field(default_factory=list)
    allowed_models: List[str] = Field(default_factory=list)
    allowed_providers: List[str] = Field(default_factory=list)
    allowed_plugins: List[str] = Field(default_factory=list)
    max_tokens: int
    max_cost: float
    max_execution_time: float
    is_active: bool
