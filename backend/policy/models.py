"""Pydantic models representing policy rules, registries, evaluations, and audit logs."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class PolicyDecision(str, Enum):
    """Allowed decisions from policy evaluation."""

    ALLOW = "allow"
    DENY = "deny"
    WARN = "warn"
    AUDIT = "audit"


class PolicyType(str, Enum):
    """Domains of applicability for policies."""

    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    SANDBOX = "sandbox"
    RATE_LIMIT = "rate_limit"
    RESOURCE = "resource"


class RuleCondition(BaseModel):
    """A conditional rule criteria matching against a context key."""

    field: str
    operator: str  # "eq" | "neq" | "gt" | "lt" | "contains" | "in"
    value: Any


class PolicyRule(BaseModel):
    """An individual policy governance rule."""

    rule_id: str
    name: str
    decision: PolicyDecision
    conditions: List[RuleCondition] = Field(default_factory=list)
    message: str = ""


class Policy(BaseModel):
    """A collection of rules governing a specific domain or target."""

    policy_id: str
    name: str
    policy_type: PolicyType
    enabled: bool = True
    rules: List[PolicyRule] = Field(default_factory=list)
    target_id: str = "*"  # Workspace ID, Organization ID, Provider ID, etc.
    created_at: str = Field(default_factory=_utcnow)


class EvaluationResult(BaseModel):
    """Decision output of a policy evaluation run."""

    decision: PolicyDecision = PolicyDecision.ALLOW
    matched_rules: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    denied_reasons: List[str] = Field(default_factory=list)
    duration_ms: float = 0.0


class AuditLogEntry(BaseModel):
    """Persistent audit record of a policy evaluation."""

    audit_id: str
    timestamp: str = Field(default_factory=_utcnow)
    user_id: str
    workspace_id: str
    organization_id: str
    action: str
    context: Dict[str, Any] = Field(default_factory=dict)
    evaluation: EvaluationResult
