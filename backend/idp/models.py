"""Pydantic data models representing scaffolding queries and code audits."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ScaffoldType(str, Enum):
    """Component template choices for project scaffolding."""

    MODULE = "module"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    AGENT = "agent"


class ScaffoldRequest(BaseModel):
    """Request details containing component categories and configuration settings."""

    scaffold_type: ScaffoldType = ScaffoldType.MODULE
    name: str
    description: Optional[str] = None
    target_directory: str = ""


class ScaffoldResult(BaseModel):
    """Outcome detailing created directory layout and boilerplate files."""

    success: bool
    generated_files: List[str] = Field(default_factory=list)
    message: Optional[str] = None


class QualityReport(BaseModel):
    """Consolidated code metrics including lints, formatter checks, and warnings."""

    formatting_passed: bool
    lint_warnings: List[str] = Field(default_factory=list)
    circular_dependencies: List[str] = Field(default_factory=list)
    architecture_score: int = 100  # [0, 100]


class CLICommandResult(BaseModel):
    """Output metrics resulting from CLI tool command executions."""

    output: str
    exit_code: int
    duration_ms: float
