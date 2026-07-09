"""Pydantic data models for the Disaster Recovery & Business Continuity framework."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class BackupType(str, Enum):
    """Supported backup strategies."""

    FULL = "full"
    INCREMENTAL = "incremental"
    METADATA = "metadata"
    MANUAL = "manual"
    SCHEDULED = "scheduled"


class RecoveryStatus(str, Enum):
    """High-level status of a recovery operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class CheckpointType(str, Enum):
    """Category of state being checkpointed."""

    WORKFLOW = "workflow"
    SESSION = "session"
    MEMORY = "memory"
    EXECUTION_CONTEXT = "execution_context"
    KNOWLEDGE = "knowledge"
    CONFIGURATION = "configuration"
    WORKSPACE = "workspace"


class FailureScenario(str, Enum):
    """Known failure scenarios the framework can recover from."""

    PROVIDER_FAILURE = "provider_failure"
    DATABASE_FAILURE = "database_failure"
    APPLICATION_RESTART = "application_restart"
    WORKER_CRASH = "worker_crash"
    NETWORK_INTERRUPTION = "network_interruption"
    PARTIAL_WORKFLOW_FAILURE = "partial_workflow_failure"


class Checkpoint(BaseModel):
    """A persisted snapshot of component state at a point in time."""

    checkpoint_id: str
    checkpoint_type: CheckpointType
    component_id: str
    state: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BackupRecord(BaseModel):
    """Record of a completed backup operation."""

    backup_id: str
    backup_type: BackupType
    components: List[str] = Field(default_factory=list)
    checkpoint_ids: List[str] = Field(default_factory=list)
    size_bytes: int = 0
    created_at: str = Field(default_factory=_utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RestoreRequest(BaseModel):
    """Parameters for a restore operation."""

    backup_id: Optional[str] = None
    checkpoint_id: Optional[str] = None
    checkpoint_type: Optional[CheckpointType] = None
    component_id: Optional[str] = None
    target_state: Optional[Dict[str, Any]] = None


class RecoveryEvent(BaseModel):
    """A single event in the recovery timeline."""

    event_id: str
    scenario: FailureScenario
    component: str
    status: RecoveryStatus = RecoveryStatus.PENDING
    detail: str = ""
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=_utcnow)


class RecoveryRun(BaseModel):
    """Complete record of one recovery operation."""

    run_id: str
    scenario: FailureScenario
    started_at: str = Field(default_factory=_utcnow)
    completed_at: str = ""
    status: RecoveryStatus = RecoveryStatus.PENDING
    recovered_components: List[str] = Field(default_factory=list)
    failed_components: List[str] = Field(default_factory=list)
    timeline: List[RecoveryEvent] = Field(default_factory=list)
    duration_ms: float = 0.0
    integrity_verified: bool = False
