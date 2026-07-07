"""Core data schemas for Persistent AI Workspace & Session Intelligence."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckpointType(str, Enum):
    """Types of session checkpoints."""
    WORKFLOW_START = "Workflow Start"
    MAJOR_MILESTONE = "Major Milestone"
    WORKFLOW_COMPLETE = "Workflow Complete"
    MANUAL_SAVE = "Manual Save"


class DecisionType(str, Enum):
    """Types of decisions tracked in project context."""
    ARCHITECTURE = "Architecture"
    IMPLEMENTATION = "Implementation"


class Decision(BaseModel):
    """Represents a design or implementation decision."""
    decision_id: str = Field(default_factory=lambda: f"dec-{uuid.uuid4().hex[:8]}")
    title: str
    description: str
    decision_type: DecisionType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    context: Dict[str, Any] = Field(default_factory=dict)


class WorkspaceMemoryModel(BaseModel):
    """Workspace state data schema."""
    current_project: Optional[str] = None
    recent_files: List[str] = Field(default_factory=list)
    recent_workflows: List[str] = Field(default_factory=list)
    recent_analyses: List[str] = Field(default_factory=list)
    current_objective: Optional[str] = None
    pending_tasks: List[str] = Field(default_factory=list)


class ProjectContextModel(BaseModel):
    """Project-level goals and roadmap context."""
    goals: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    architecture_decisions: List[Decision] = Field(default_factory=list)
    implementation_decisions: List[Decision] = Field(default_factory=list)
    known_issues: List[str] = Field(default_factory=list)
    technical_debt: List[str] = Field(default_factory=list)


class ReasoningStepModel(BaseModel):
    """Reasoning step matching the session context."""
    step_id: str = Field(default_factory=lambda: f"rs-{uuid.uuid4().hex[:8]}")
    description: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = 1.0


class ReasoningHistoryModel(BaseModel):
    """Captured logs of AI teammate's cognitive steps."""
    questions_asked: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)
    reasoning_steps: List[ReasoningStepModel] = Field(default_factory=list)
    generated_reports: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    confidence_evolution: List[float] = Field(default_factory=list)


class CheckpointModel(BaseModel):
    """A checkpoint storing the serialized session state at a specific time."""
    checkpoint_id: str = Field(default_factory=lambda: f"chk-{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    checkpoint_type: CheckpointType
    workspace_memory: WorkspaceMemoryModel
    project_context: ProjectContextModel
    reasoning_history: ReasoningHistoryModel
    description: str = ""


class SessionSummaryModel(BaseModel):
    """Summary of actions completed during a session."""
    completed: List[str] = Field(default_factory=list)
    current_progress: str = ""
    next_recommended_actions: List[str] = Field(default_factory=list)
    open_issues: List[str] = Field(default_factory=list)


class SessionTimelineEvent(BaseModel):
    """Timeline entry for any action taken in a session."""
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    event_type: str
    description: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class SessionModel(BaseModel):
    """Top-level session model."""
    session_id: str = Field(default_factory=lambda: f"sess-{uuid.uuid4().hex[:8]}")
    name: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    restored_at: Optional[str] = None
    workspace_memory: WorkspaceMemoryModel = Field(default_factory=WorkspaceMemoryModel)
    project_context: ProjectContextModel = Field(default_factory=ProjectContextModel)
    reasoning_history: ReasoningHistoryModel = Field(default_factory=ReasoningHistoryModel)
    checkpoints: List[CheckpointModel] = Field(default_factory=list)
    timeline: List[SessionTimelineEvent] = Field(default_factory=list)
