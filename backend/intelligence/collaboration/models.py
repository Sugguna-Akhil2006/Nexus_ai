"""Data models representing AgentTask, CollaborationSession, and CollaborationReport structures."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentTask(BaseModel):
    """A task delegator request dispatched from one agent to another."""
    task_id: str
    sender_agent: str
    receiver_agent: str
    description: str
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CollaborationSession(BaseModel):
    """Execution state of a single multi-agent collaboration session."""
    session_id: str
    workspace_id: str
    objective: str
    status: str = "RUNNING"  # RUNNING, COMPLETED, FAILED
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class CollaborationReport(BaseModel):
    """Consolidated results compiled after multi-agent collaboration runs."""
    report_id: str
    session_id: str
    objective: str
    executed_agents: List[str] = Field(default_factory=list)
    shared_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_conclusions: List[str] = Field(default_factory=list)
    confidence_score: float = 1.0
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
