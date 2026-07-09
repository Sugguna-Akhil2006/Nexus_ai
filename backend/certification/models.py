"""Pydantic models for the Platform Certification Suite."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CertificationLevel(str, Enum):
    """Tiered certification levels awarded based on overall score."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    ENTERPRISE = "enterprise"
    NONE = "none"


class CheckStatus(str, Enum):
    """Individual certification check outcome."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class CertificationDomain(str, Enum):
    """Top-level subsystem domains covered by certification."""

    RUNTIME = "runtime"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    KNOWLEDGE = "knowledge"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class CheckResult(BaseModel):
    """Outcome of a single atomic certification check."""

    name: str
    domain: CertificationDomain
    status: CheckStatus = CheckStatus.PASSED
    message: str = ""
    duration_ms: float = 0.0
    critical: bool = False


class DomainReport(BaseModel):
    """Aggregated results for one certification domain."""

    domain: CertificationDomain
    checks: List[CheckResult] = Field(default_factory=list)
    score: int = 100  # 0-100
    warnings: List[str] = Field(default_factory=list)
    critical_failures: List[str] = Field(default_factory=list)

    @property
    def passed(self) -> int:
        """Number of checks that passed."""
        return sum(1 for c in self.checks if c.status == CheckStatus.PASSED)

    @property
    def failed(self) -> int:
        """Number of checks that failed."""
        return sum(1 for c in self.checks if c.status == CheckStatus.FAILED)


class CertificationRun(BaseModel):
    """Full certification run record with all domain reports and final verdict."""

    run_id: str
    started_at: str
    completed_at: str = ""
    domain_reports: List[DomainReport] = Field(default_factory=list)
    overall_score: int = 0
    certification_level: CertificationLevel = CertificationLevel.NONE
    total_checks: int = 0
    total_passed: int = 0
    total_failed: int = 0
    total_warnings: int = 0
    recommended_improvements: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
