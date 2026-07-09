"""Pydantic models for the Compatibility & Migration Framework."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class MigrationStatus(str, Enum):
    """Lifecycle state of a migration step or full run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class MigrationKind(str, Enum):
    """Category of migration being performed."""

    SCHEMA = "schema"
    CONFIG = "config"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    DATA = "data"


class BreakingChangeSeverity(str, Enum):
    """How disruptive a detected breaking change is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CompatibilityStatus(str, Enum):
    """Overall compatibility verdict between two versions."""

    COMPATIBLE = "compatible"
    COMPATIBLE_WITH_WARNINGS = "compatible_with_warnings"
    INCOMPATIBLE = "incompatible"


# ---------------------------------------------------------------------------
# Core domain objects
# ---------------------------------------------------------------------------

class MigrationStep(BaseModel):
    """One discrete migration action within a migration plan."""

    step_id: str
    kind: MigrationKind
    description: str
    from_version: str
    to_version: str
    status: MigrationStatus = MigrationStatus.PENDING
    duration_ms: float = 0.0
    error: Optional[str] = None
    applied_at: Optional[str] = None


class MigrationPlan(BaseModel):
    """Ordered sequence of migration steps to move from one version to another."""

    plan_id: str
    from_version: str
    to_version: str
    steps: List[MigrationStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MigrationRun(BaseModel):
    """Complete record of a migration execution, including steps and outcomes."""

    run_id: str
    plan_id: str
    from_version: str
    to_version: str
    status: MigrationStatus = MigrationStatus.PENDING
    steps: List[MigrationStep] = Field(default_factory=list)
    started_at: str = Field(default_factory=_utcnow)
    completed_at: str = ""
    duration_ms: float = 0.0
    errors: List[str] = Field(default_factory=list)
    can_rollback: bool = True


class BreakingChange(BaseModel):
    """A detected breaking change between two API or configuration versions."""

    change_id: str
    kind: str  # "removed_api" | "renamed_api" | "config_change" | "dependency" | "deprecated"
    location: str  # module.class.method or config key path
    description: str
    severity: BreakingChangeSeverity = BreakingChangeSeverity.MEDIUM
    from_version: str
    to_version: str
    migration_hint: str = ""


class CompatibilityReport(BaseModel):
    """Compatibility verdict between an installed version and a target version."""

    report_id: str
    from_version: str
    to_version: str
    status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE
    breaking_changes: List[BreakingChange] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)


class RollbackRecord(BaseModel):
    """Record of a completed rollback operation."""

    rollback_id: str
    run_id: str
    rolled_back_steps: List[str] = Field(default_factory=list)
    status: MigrationStatus = MigrationStatus.ROLLED_BACK
    executed_at: str = Field(default_factory=_utcnow)
    detail: str = ""
