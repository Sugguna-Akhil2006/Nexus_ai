"""Read-only DTO schemas that power the developer dashboard API responses."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ExecutionTimelineView(BaseModel):
    """Chronological list of events for an execution."""
    execution_id: str
    events: List[Dict[str, Any]] = Field(default_factory=list)
    total_duration_ms: float = 0.0


class AgentTimelineView(BaseModel):
    """Per-agent span breakdown for an execution."""
    execution_id: str
    agents: List[Dict[str, Any]] = Field(default_factory=list)


class LatencyChartView(BaseModel):
    """Module latency data points suitable for charting."""
    module_timings: Dict[str, float] = Field(default_factory=dict)
    slowest_operations: List[Dict[str, Any]] = Field(default_factory=list)
    avg_latency_ms: float = 0.0


class TokenUsageView(BaseModel):
    """Token consumption summary across providers and models."""
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    by_model: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class ProviderStatsView(BaseModel):
    """Aggregated statistics per AI provider."""
    provider: str
    total_invocations: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    failure_rate: float = 0.0


class FailureReportView(BaseModel):
    """Summary of captured failure records for an execution."""
    execution_id: str
    failures: List[Dict[str, Any]] = Field(default_factory=list)
    total_failures: int = 0


class ModuleHealthView(BaseModel):
    """Health indicators per intelligence module."""
    module: str
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    invocation_count: int = 0


class DashboardView(BaseModel):
    """Composite dashboard data returned for a single execution."""
    execution_timeline: ExecutionTimelineView
    agent_timeline: AgentTimelineView
    latency_chart: LatencyChartView
    token_usage: TokenUsageView
    failure_report: FailureReportView
