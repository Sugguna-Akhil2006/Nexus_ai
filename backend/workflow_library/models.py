"""Pydantic data models representing workflow templates, versions, and schedules."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class TemplateScope(str, Enum):
    """Access sharing scope defined on a workflow template."""

    PRIVATE = "private"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    MARKETPLACE = "marketplace"


class WorkflowTemplate(BaseModel):
    """A reusable, versioned AI workflow pipeline automation template."""

    template_id: str
    name: str
    description: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    scope: TemplateScope = TemplateScope.PRIVATE
    version: str = "1.0.0"
    author: str = "System"
    created_at: str


class TemplateVersion(BaseModel):
    """A historical snapshot representing a single template version."""

    version: str
    template_id: str
    steps: List[str] = Field(default_factory=list)
    changelog: Optional[str] = None
    created_at: str


class AutomationSchedule(BaseModel):
    """Cron scheduling settings for automated template runs."""

    schedule_id: str
    template_id: str
    cron_expression: str  # e.g. "0 9 * * 1-5"
    enabled: bool = True
    next_run_at: Optional[str] = None


class ExecutedTemplateLog(BaseModel):
    """Historical execution summary log from runs."""

    execution_id: str
    template_id: str
    status: str  # "success" | "failed"
    started_at: str
    duration_ms: float
