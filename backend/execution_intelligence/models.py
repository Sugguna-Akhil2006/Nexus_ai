"""Core Pydantic models for AI Execution Intelligence & Optimization Engine."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BottleneckType(str, Enum):
    """Supported bottleneck classification types."""
    SLOW_MODULE = "Slow Module"
    HIGH_RETRY = "High Retry"
    REPEATED_FAILURES = "Repeated Failures"
    EXPENSIVE_PROVIDER = "Expensive Provider"
    LARGE_PROMPTS = "Large Prompts"
    DUPLICATE_OPERATIONS = "Duplicate Operations"


class RecommendationCategory(str, Enum):
    """Categories for optimization suggestions."""
    ALTERNATIVE_MODELS = "Alternative Models"
    WORKFLOW_RESTRUCTURING = "Workflow Restructuring"
    CACHING_OPPORTUNITIES = "Caching Opportunities"
    PARALLEL_EXECUTION = "Parallel Execution"
    PROMPT_OPTIMIZATION = "Prompt Optimization"
    CONTEXT_REDUCTION = "Context Reduction"
    CONNECTOR_IMPROVEMENTS = "Connector Improvements"


class ImpactLevel(str, Enum):
    """Estimated performance or cost impact level."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class ExecutionMetricsModel(BaseModel):
    """Aggregated execution metrics for analysis."""
    workflow_id: str
    execution_count: int = 0
    total_duration_ms: float = 0.0
    average_duration_ms: float = 0.0
    module_execution_times: Dict[str, float] = Field(default_factory=dict)  # module_name -> total_ms
    retry_counts: int = 0
    failures_count: int = 0
    fallback_usage_count: int = 0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    estimated_cost_usd: float = 0.0
    average_memory_usage_mb: float = 0.0
    provider_latencies: Dict[str, List[float]] = Field(default_factory=dict)  # provider_name -> list of latencies


class BottleneckModel(BaseModel):
    """Represents a detected performance or cost bottleneck."""
    bottleneck_id: str
    type: BottleneckType
    target: str  # e.g., module name, provider name, or step ID
    description: str
    metric_value: float
    impact_level: ImpactLevel


class RecommendationModel(BaseModel):
    """Actionable advice suggesting workflow improvements."""
    recommendation_id: str
    category: RecommendationCategory
    description: str
    rationale: str
    estimated_speedup_pct: float = 0.0
    estimated_cost_reduction_usd: float = 0.0
    impact_level: ImpactLevel


class FailurePredictionModel(BaseModel):
    """Stochastic estimation of potential failure risks."""
    failure_probability: float = 0.0  # 0.0 to 1.0
    likely_bottlenecks: List[str] = Field(default_factory=list)
    resource_exhaustion_probability: float = 0.0
    timeout_risk_pct: float = 0.0
    provider_instability_index: float = 0.0  # 0.0 (stable) to 1.0 (unstable)


class ResourceOptimizationModel(BaseModel):
    """Recommended system parameter allocations."""
    recommended_cpu_cores: float = 0.0
    recommended_memory_mb: float = 0.0
    gpu_utilization_target_pct: float = 0.0
    queue_balancing_strategy: str = "Standard Round-Robin"
    worker_distribution: Dict[str, int] = Field(default_factory=dict)  # queue_name -> worker count


class ExecutionOptimizationReportModel(BaseModel):
    """Comprehensive performance and cost optimization report."""
    report_id: str
    workflow_id: str
    timestamp: str
    current_metrics: ExecutionMetricsModel
    detected_bottlenecks: List[BottleneckModel] = Field(default_factory=list)
    optimization_suggestions: List[RecommendationModel] = Field(default_factory=list)
    failure_prediction: FailurePredictionModel
    resource_recommendations: ResourceOptimizationModel
    estimated_performance_gain_pct: float = 0.0
    estimated_cost_reduction_usd: float = 0.0
