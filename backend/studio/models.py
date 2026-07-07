"""Data models representing developer experience artifacts, graphs, and system snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceInfo:
    """Developer workspace general specs."""

    workspace_id: str
    name: str
    created_at: str
    member_count: int
    active_jobs_count: int


@dataclass
class AgentInspection:
    """Detailed structural inspector payload for registered agents."""

    agent_id: str
    name: str
    capabilities: List[str]
    health_status: str
    current_tasks: List[str] = field(default_factory=list)
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowNode:
    """Node inside visual workflow graph representation."""

    node_id: str
    label: str
    type: str  # task, parallel, decision, end
    status: str  # pending, running, completed, failed
    duration_ms: float = 0.0
    error_message: Optional[str] = None


@dataclass
class WorkflowInspection:
    """Graph structure trace representing an active execution pipeline."""

    workflow_id: str
    name: str
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[Dict[str, str]] = field(default_factory=list)  # source to target mappings
    total_execution_time_ms: float = 0.0


@dataclass
class MemorySnapshot:
    """Unified capture of short-term, long-term, and profile variables."""

    workspace_id: str
    short_term: Dict[str, Any] = field(default_factory=dict)
    long_term: Dict[str, Any] = field(default_factory=dict)
    knowledge_profile: Dict[str, Any] = field(default_factory=dict)
    memory_usage_bytes: int = 0


@dataclass
class PromptTemplate:
    """Prompt template entry inside studio prompt library."""

    prompt_id: str
    category: str
    version: str
    template: str
    example_outputs: List[str] = field(default_factory=list)
    usage_count: int = 0


@dataclass
class PluginStatus:
    """System status representation of plugin extensions."""

    plugin_id: str
    name: str
    version: str
    is_enabled: bool
    description: str


@dataclass
class ProviderMetrics:
    """Realtime monitoring metrics for model and embedding providers."""

    provider_id: str
    name: str
    type: str  # llm or embedding
    latency_ms: float
    cost_per_1k_tokens: float
    availability_pct: float
    usage_count: int
