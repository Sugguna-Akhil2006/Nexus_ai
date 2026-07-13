"""Pydantic data models for the Dynamic Cross-Intelligence Orchestrator."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.intelligence.contracts.response_models import Artifact, Citation, Recommendation
from backend.intelligence.orchestrator.execution_policy import ExecutionPolicy


class NodeStatus(str, Enum):
    """Lifecycle status of a single execution node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionNode(BaseModel):
    """A single module execution task in the plan graph.

    Attributes:
        node_id: Unique task identifier.
        module_name: Target intelligence module name.
        capability: Required capability.
        dependencies: list of node_ids that must complete successfully first.
        status: Current task execution status.
        result: Ingested output report on completion.
        error: Captured failure message.
        duration_ms: Total duration in milliseconds.
    """

    node_id: str = Field(default_factory=lambda: f"node-{uuid.uuid4().hex[:8]}")
    module_name: str
    capability: str
    dependencies: List[str] = Field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: float = 0.0


class ExecutionGraph(BaseModel):
    """The directed acyclic graph (DAG) representing the execution flow."""

    graph_id: str = Field(default_factory=lambda: f"graph-{uuid.uuid4().hex[:10]}")
    nodes: Dict[str, ExecutionNode] = Field(default_factory=dict)
    edges: List[tuple[str, str]] = Field(default_factory=list)  # (from_node, to_node)


class ExecutionStep(BaseModel):
    """A step inside the execution plan."""
    step_id: str
    module_name: str
    action: str


class OrchestrationPlan(BaseModel):
    """Consolidated plan with execution graph and optimizer policy settings."""

    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:10]}")
    graph: ExecutionGraph = Field(default_factory=ExecutionGraph)
    policy: ExecutionPolicy = Field(default_factory=ExecutionPolicy)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    steps: List[ExecutionStep] = Field(default_factory=list)
    execution_mode: str = "PARALLEL"



class OrchestrationContextDetails(BaseModel):
    """Lightweight metadata context for the orchestration run."""

    workspace_id: str
    user_id: str
    session_id: Optional[str] = None
    query: str
    document_ids: List[str] = Field(default_factory=list)


class OrchestratedResult(BaseModel):
    """Aggregated outcome of a dynamic cross-intelligence request execution."""

    orchestration_id: str = Field(default_factory=lambda: f"orch-{uuid.uuid4().hex[:12]}")
    request_id: str
    plan_id: str
    status: str  # "completed" | "partial" | "failed"
    graph: ExecutionGraph

    # Synthesized results
    reasoning_summary: str = ""
    combined_results: Dict[str, Any] = Field(default_factory=dict)
    citations: List[Citation] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    recommendations: List[Recommendation] = Field(default_factory=list)

    # Telemetry and diagnostics
    modules_executed: List[str] = Field(default_factory=list)
    execution_timeline: Dict[str, float] = Field(default_factory=dict)  # step_id -> duration_ms
    confidence_score: float = 0.0
    errors: Dict[str, str] = Field(default_factory=dict)  # module_name -> error_msg
    completed_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OrchestrationRequest(BaseModel):
    """Payload representing a client request for the orchestrator."""

    workspace_id: str
    user_id: str
    query: str
    document_ids: List[str] = Field(default_factory=list)
    options: Dict[str, Any] = Field(default_factory=dict)


class UnifiedIntelligenceResponse(BaseModel):
    """Payload representing the formatted response from the orchestrator."""

    response_id: str
    modules_executed: List[str]
    execution_timeline: List[Dict[str, Any]]
    evidence_sources: List[Any]
    confidence_score: float
    reasoning_summary: str
    final_response: str

