"""Pydantic data models for secure execution sandbox sessions and command outcomes."""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class SandboxConfig(BaseModel):
    """Configuration constraints defining sandbox isolation parameters."""

    allowed_commands: List[str] = Field(default_factory=lambda: ["python", "pip", "git", "echo", "dir", "ls"])
    blocked_commands: List[str] = Field(default_factory=lambda: ["rm", "del", "format", "shutdown", "kill"])
    timeout_seconds: float = 30.0
    max_memory_mb: int = 512
    allowed_root_path: str = ""
    env_vars: Dict[str, str] = Field(default_factory=dict)


class CommandResult(BaseModel):
    """Output results of executing a script or shell command in the sandbox."""

    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    generated_files: List[str] = Field(default_factory=list)


class SandboxSessionInfo(BaseModel):
    """Session details tracking isolated directories."""

    session_id: str
    status: str  # "active" | "terminated"
    working_directory: str
    config: SandboxConfig = Field(default_factory=SandboxConfig)
    created_at: str
