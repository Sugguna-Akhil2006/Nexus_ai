"""Data schemas defining LLM models, provider statuses, quotas, and feature flags."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ModelProfile:
    """Represents a registered LLM model profile configuration."""

    model_id: str
    name: str
    provider_id: str
    version: str
    capabilities: List[str] = field(default_factory=list)
    is_active: bool = True
    is_default: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderProfile:
    """Represents a model provider registry entry."""

    provider_id: str
    name: str
    is_active: bool = True
    api_url: Optional[str] = None
    health_status: str = "healthy"
    error_rate: float = 0.0


@dataclass
class QuotaPolicy:
    """Rules defining monthly/daily execution token and cost limits."""

    policy_id: str
    workspace_id: str = "*"
    user_id: str = "*"
    daily_token_limit: int = 100000
    monthly_token_limit: int = 1000000
    daily_cost_limit: float = 5.0
    monthly_cost_limit: float = 50.0


@dataclass
class UsageMetrics:
    """Aggregated usage metrics tracking billing costs and token frequencies."""

    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    average_latency_ms: float = 0.0
    error_count: int = 0


@dataclass
class FeatureFlag:
    """System runtime operational feature flags."""

    flag_id: str
    name: str
    is_enabled: bool = False
    workspace_level_overrides: Dict[str, bool] = field(default_factory=dict)
    description: str = ""
