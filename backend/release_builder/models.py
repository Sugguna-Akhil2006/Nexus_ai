"""Pydantic data models for release candidate manifesting and artifact tracking."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ReleaseType(str, Enum):
    """Semantic versioning category types."""

    RC = "rc"
    STABLE = "stable"
    HOTFIX = "hotfix"
    NIGHTLY = "nightly"


class VersionInfo(BaseModel):
    """Parsed semantic version details."""

    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None
    build_metadata: Optional[str] = None


class ReleaseManifest(BaseModel):
    """Meta-information descriptor saved in release packages."""

    version: str
    git_commit: str
    build_date: str
    dependencies: List[str] = Field(default_factory=list)
    supported_providers: List[str] = Field(default_factory=list)


class ReleaseArtifact(BaseModel):
    """Packaged build distribution asset file details."""

    name: str
    artifact_type: str  # "source" | "docker" | "python" | "config" | "docs"
    sha256: str
    size_bytes: int


class BuildHistoryRecord(BaseModel):
    """Historical record detailing completed release builds."""

    build_id: str
    version: str
    status: str  # "success" | "failed"
    artifacts: List[ReleaseArtifact] = Field(default_factory=list)
    manifest: Optional[ReleaseManifest] = None
    created_at: str
