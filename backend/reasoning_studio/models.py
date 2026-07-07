"""Pydantic models for Nexus AI Reasoning Studio."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ReplayState(str, Enum):
    """Lifecycle state of a replay session."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class NodeType(str, Enum):
    """Decision-graph node classification."""

    DECISION = "decision"
    EVIDENCE = "evidence"
    CONCLUSION = "conclusion"
    TOOL_CALL = "tool_call"
    MEMORY_LOOKUP = "memory_lookup"
    KNOWLEDGE_QUERY = "knowledge_query"
    PROVIDER_RESPONSE = "provider_response"


class DiffStatus(str, Enum):
    """Line-level diff classification."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


# ---------------------------------------------------------------------------
# Captured reasoning artefact
# ---------------------------------------------------------------------------


class CapturedReasoningStep(BaseModel):
    """Enriched reasoning step stored in the Studio trace store.

    Wraps the upstream ``ReasoningStep`` and adds Studio-specific fields
    (prompt version, tool invocations, provider response, knowledge queries)
    without duplicating the Observability trace collection logic.
    """

    step_id: str = Field(default_factory=lambda: f"crs-{uuid.uuid4().hex[:8]}")
    source_step_id: str = ""  # links to ReasoningStep.step_id
    execution_id: str
    description: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    intermediate_conclusions: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)  # KnowledgeSourceRef IDs
    confidence: float = 1.0
    prompt_version: str = ""
    tool_invocations: List[str] = Field(default_factory=list)
    provider_response_summary: str = ""
    memory_lookups: List[str] = Field(default_factory=list)
    knowledge_queries: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    sequence_index: int = 0


class StudioTrace(BaseModel):
    """Full reasoning trace stored in the Studio, enriched over the raw ExecutionTrace."""

    studio_trace_id: str = Field(default_factory=lambda: f"st-{uuid.uuid4().hex[:8]}")
    execution_id: str
    workflow_id: str = ""
    workspace_id: str = ""
    steps: List[CapturedReasoningStep] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    total_steps: int = 0
    final_confidence: float = 0.0
    tags: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Replay
# ---------------------------------------------------------------------------


class ReplaySession(BaseModel):
    """Represents a developer replay session over a StudioTrace."""

    session_id: str = Field(default_factory=lambda: f"rep-{uuid.uuid4().hex[:8]}")
    studio_trace_id: str
    execution_id: str
    state: ReplayState = ReplayState.IDLE
    current_step_index: int = 0
    total_steps: int = 0
    started_at: Optional[str] = None
    paused_at: Optional[str] = None
    completed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# Decision graph
# ---------------------------------------------------------------------------


class GraphNode(BaseModel):
    """A node in the decision/evidence/reasoning graph."""

    node_id: str = Field(default_factory=lambda: f"node-{uuid.uuid4().hex[:8]}")
    node_type: NodeType
    label: str
    description: str = ""
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """A directed edge connecting two graph nodes."""

    edge_id: str = Field(default_factory=lambda: f"edge-{uuid.uuid4().hex[:8]}")
    source_node_id: str
    target_node_id: str
    label: str = ""
    weight: float = 1.0


class DecisionGraph(BaseModel):
    """Complete decision / evidence reasoning graph for one trace."""

    graph_id: str = Field(default_factory=lambda: f"dg-{uuid.uuid4().hex[:8]}")
    studio_trace_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Evidence visualizer
# ---------------------------------------------------------------------------


class EvidenceNode(BaseModel):
    """A single piece of evidence surfaced during reasoning."""

    evidence_id: str = Field(default_factory=lambda: f"ev-{uuid.uuid4().hex[:8]}")
    source_type: str  # "document" | "ukp" | "graph" | "memory" | "tool"
    source_identifier: str
    content_summary: str
    confidence: float = 1.0
    knowledge_fabric_ref: Optional[str] = None
    related_step_ids: List[str] = Field(default_factory=list)


class EvidenceTree(BaseModel):
    """Hierarchical evidence tree for a trace."""

    tree_id: str = Field(default_factory=lambda: f"etree-{uuid.uuid4().hex[:8]}")
    studio_trace_id: str
    root_evidence: List[EvidenceNode] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Confidence analysis
# ---------------------------------------------------------------------------


class ConfidencePoint(BaseModel):
    """A single (step, confidence) data point in the confidence timeline."""

    step_index: int
    step_id: str
    description: str
    confidence: float
    timestamp: str


class ConfidenceAnalysis(BaseModel):
    """Full confidence evolution analysis for a trace."""

    analysis_id: str = Field(default_factory=lambda: f"ca-{uuid.uuid4().hex[:8]}")
    studio_trace_id: str
    timeline: List[ConfidencePoint] = Field(default_factory=list)
    min_confidence: float = 1.0
    max_confidence: float = 0.0
    average_confidence: float = 0.0
    drops: List[int] = Field(default_factory=list)   # step indices where confidence dropped
    peaks: List[int] = Field(default_factory=list)   # step indices where confidence peaked


# ---------------------------------------------------------------------------
# Trace comparator / diff
# ---------------------------------------------------------------------------


class DiffEntry(BaseModel):
    """A single compared unit between two traces."""

    index: int
    status: DiffStatus
    left_value: Optional[str] = None
    right_value: Optional[str] = None
    field: str = ""


class TraceDiff(BaseModel):
    """Result of comparing two Studio traces."""

    diff_id: str = Field(default_factory=lambda: f"diff-{uuid.uuid4().hex[:8]}")
    left_trace_id: str
    right_trace_id: str
    step_diffs: List[DiffEntry] = Field(default_factory=list)
    confidence_diffs: List[DiffEntry] = Field(default_factory=list)
    provider_diffs: List[DiffEntry] = Field(default_factory=list)
    total_changed: int = 0
    similarity_score: float = 1.0  # 1.0 = identical, 0.0 = completely different


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


class Explanation(BaseModel):
    """Human-readable explanations for a reasoning artefact."""

    explanation_id: str = Field(default_factory=lambda: f"exp-{uuid.uuid4().hex[:8]}")
    studio_trace_id: str
    why_this_decision: str = ""
    why_this_provider: str = ""
    why_this_workflow: str = ""
    why_this_confidence: str = ""
    summary: str = ""
