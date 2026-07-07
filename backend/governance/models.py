"""Models and data schemas for AI Governance, Policy & Security Framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    """Execution risk classifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalType(str, Enum):
    """Enforces dynamic execution approval routes."""

    AUTO = "automatic"
    MANUAL = "manual"
    ADMIN = "admin"
    SCHEDULED = "scheduled"


@dataclass
class PolicyRule:
    """Configurable constraint rule verified by the policy engine."""

    policy_id: str
    name: str
    workspace_id: str = "*"  # Wildcard for all workspaces
    allowed_modules: List[str] = field(default_factory=lambda: ["*"])
    allowed_models: List[str] = field(default_factory=lambda: ["*"])
    allowed_providers: List[str] = field(default_factory=lambda: ["*"])
    allowed_plugins: List[str] = field(default_factory=lambda: ["*"])
    max_tokens: int = 4096
    max_cost: float = 0.50
    max_execution_time: float = 60.0  # seconds
    is_active: bool = True


@dataclass
class SecurityCheckResult:
    """Consolidated security alerts and validations."""

    has_prompt_injection: bool = False
    detected_pii: List[str] = field(default_factory=list)
    has_unsafe_tools: bool = False
    has_unauthorized_plugin: bool = False
    is_malicious_file: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    """Risk scoring and classification payload."""

    risk_level: RiskLevel
    score: float  # 0.0 to 1.0
    explanation: str
    checks_evaluated: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditRecord:
    """Comprehensive historical trail for audit logs."""

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
    status: str  # approved, completed, denied, failed
    policy_violations: List[str] = field(default_factory=list)
    security_alerts: List[str] = field(default_factory=list)
    risk_level: str = "low"


@dataclass
class GovernanceDecision:
    """Consolidated policy check decision returned prior to run."""

    is_approved: bool
    risk_level: RiskLevel
    approval_type: ApprovalType
    decision_reasons: List[str] = field(default_factory=list)
    security_check: Optional[SecurityCheckResult] = None
    risk_assessment: Optional[RiskAssessment] = None


@dataclass
class ComplianceStatus:
    """State status for standard industry policies."""

    gdpr_compliant: bool = True
    soc2_compliant: bool = True
    iso_compliant: bool = True
    enterprise_compliant: bool = True
    non_compliant_reasons: List[str] = field(default_factory=list)
