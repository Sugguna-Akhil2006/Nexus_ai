"""Pydantic data models for the Architecture Knowledge Center."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ModuleMetadata(BaseModel):
    """Catalog metadata auto-extracted for an intelligence module."""

    name: str
    purpose: str
    owner: str = "Lead AI Architect"
    dependencies: List[str] = Field(default_factory=list)
    public_apis: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    related_tests: List[str] = Field(default_factory=list)


class DependencyNode(BaseModel):
    """Component node within the dependency map."""

    node_id: str
    label: str
    type: str  # "core" | "workflow" | "orchestrator" | "module" | "knowledge"


class DependencyEdge(BaseModel):
    """Adjacency edge link representing module interactions."""

    from_node: str
    to_node: str


class DependencyGraph(BaseModel):
    """Diagram structure detailing subsystem interaction topologies."""

    nodes: List[DependencyNode] = Field(default_factory=list)
    edges: List[DependencyEdge] = Field(default_factory=list)
    mermaid_diagram: str = ""


class SequenceStep(BaseModel):
    """A single actor-to-actor request message in a sequence flow."""

    sender: str
    receiver: str
    message: str


class SequenceFlow(BaseModel):
    """A sequence scenario detailing message passing."""

    flow_name: str
    steps: List[SequenceStep] = Field(default_factory=list)
    mermaid_diagram: str = ""


class APIEndpointInfo(BaseModel):
    """Documentation record mapping to a FastAPI REST/WebSocket endpoint."""

    path: str
    method: str  # "GET" | "POST" | "WS"
    summary: str
    parameters: List[str] = Field(default_factory=list)


class DecisionRecord(BaseModel):
    """Architecture Decision Record (ADR) detailing design rationale."""

    decision_id: str
    title: str
    reason: str
    alternatives: List[str] = Field(default_factory=list)
    consequences: str
    owner: str
    date: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y-%m-%d"))
