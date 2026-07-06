"""Core Pydantic data schemas for the AI Workflow Automation Engine."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepType(str, Enum):
    """Supported intelligence module step types."""
    RESUME = "RESUME"
    GITHUB = "GITHUB"
    DOCUMENT = "DOCUMENT"
    RESEARCH = "RESEARCH"
    REASONING = "REASONING"
    KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"
    CUSTOM_PLUGIN = "CUSTOM_PLUGIN"
    NO_OP = "NO_OP"  # Used for testing and placeholder steps


class ExecutionStatus(str, Enum):
    """Possible states for a workflow or individual step execution."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMED_OUT = "TIMED_OUT"
    SKIPPED = "SKIPPED"


class WorkflowStep(BaseModel):
    """Definition of a single step within a workflow."""
    step_id: str = Field(default_factory=lambda: f"step-{uuid.uuid4().hex[:8]}")
    name: str
    step_type: StepType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = 0
    timeout_seconds: float = 30.0
    condition: Optional[str] = None  # Python expression evaluated against context vars
    depends_on: List[str] = Field(default_factory=list)


class ParallelBranch(BaseModel):
    """A group of steps that execute concurrently."""
    branch_id: str = Field(default_factory=lambda: f"branch-{uuid.uuid4().hex[:8]}")
    name: str = "parallel_branch"
    steps: List[WorkflowStep] = Field(default_factory=list)


class WorkflowDefinition(BaseModel):
    """Full declarative specification of a workflow."""
    workflow_id: str = Field(default_factory=lambda: f"wf-{uuid.uuid4().hex[:8]}")
    name: str
    description: str = ""
    steps: List[WorkflowStep] = Field(default_factory=list)
    parallel_branches: List[ParallelBranch] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class StepResult(BaseModel):
    """Result record produced after a single step execution."""
    step_id: str
    step_name: str
    status: ExecutionStatus
    output: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    attempts: int = 1
    duration_seconds: float = 0.0
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: str = ""


class WorkflowExecution(BaseModel):
    """Runtime record of a single workflow execution instance."""
    execution_id: str = Field(default_factory=lambda: f"exec-{uuid.uuid4().hex[:8]}")
    workflow_id: str
    workflow_name: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    step_results: List[StepResult] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ended_at: str = ""
    duration_seconds: float = 0.0
