"""Pydantic data models representing tenants, custom settings, and resource quotas."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Lifecycle status states of an organization tenant."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class TenantSettings(BaseModel):
    """Custom settings and themes defined per-tenant."""

    theme: str = "dark"
    allowed_models: List[str] = Field(default_factory=lambda: ["gpt-4", "claude-3", "gemini-1.5"])
    security_policy: str = "standard"
    retention_days: int = 365


class TenantLimits(BaseModel):
    """Resource quotas and bounds enforced on tenant operations."""

    storage_limit_mb: int = 1024 * 10  # 10GB default
    api_rate_limit: int = 120  # requests per minute
    token_limit_monthly: int = 10_000_000
    max_concurrent_jobs: int = 5


class Tenant(BaseModel):
    """An organization tenant containing metadata, settings, and quotas."""

    tenant_id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    settings: TenantSettings = Field(default_factory=TenantSettings)
    limits: TenantLimits = Field(default_factory=TenantLimits)
    created_at: str
