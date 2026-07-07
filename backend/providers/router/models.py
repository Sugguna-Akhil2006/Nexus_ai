"""Data models representing inference requests, recommendations, and execution statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class InferenceRequest:
    """Request parameters for routing evaluation."""

    task_type: str  # chat, extraction, embedding, code_gen
    required_capabilities: List[str] = field(default_factory=list)
    min_context_length: int = 4096
    requires_streaming: bool = False
    policy_preference: str = "balanced"  # cost, quality, latency, balanced
    workspace_id: str = "default"


@dataclass
class RouterRecommendation:
    """Selected model recommendation details returned by the Routing Engine."""

    model_id: str
    provider_id: str
    estimated_cost: float
    estimated_latency_ms: float
    quality_rank: int
    fallback_applied: bool = False


@dataclass
class RouterExecutionStats:
    """Actual runtime parameters reported after model invocation completes."""

    model_id: str
    provider_id: str
    tokens_used: int
    actual_cost: float
    actual_latency_ms: float
    is_success: bool = True
    error_message: Optional[str] = None
