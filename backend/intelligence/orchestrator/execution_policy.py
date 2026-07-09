"""Execution policies for the Cross-Intelligence Orchestrator.

Defines standard trade-offs (Fastest, Quality, Cost, Balanced) and their options.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class PolicyType(str, Enum):
    """Supported intelligence module execution policies."""

    FASTEST = "fastest"
    HIGHEST_QUALITY = "highest_quality"
    LOWEST_COST = "lowest_cost"
    BALANCED = "balanced"
    CUSTOM = "custom"


class ExecutionPolicy(BaseModel):
    """Configuration options governing execution graph generation and run traits."""

    policy_type: PolicyType = PolicyType.BALANCED
    max_concurrency: int = 4
    timeout_seconds: float = 60.0
    fail_fast: bool = False
    cache_preferred: bool = True
    min_confidence_threshold: float = 0.5
    cost_limit_usd: float = 1.0
    custom_settings: dict = Field(default_factory=dict)
