"""Data schemas representing registered AI capabilities, version histories, and health metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class CapabilityType(str, Enum):
    """Supported registry capability classifications."""

    MODULE = "module"
    AGENT = "agent"
    LLM_PROVIDER = "llm_provider"
    EMBEDDING_PROVIDER = "embedding_provider"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    TOOL = "tool"
    PLUGIN = "plugin"
    CONNECTOR = "connector"
    EXPORTER = "exporter"


@dataclass
class SemVer:
    """Semantic versioning representation."""

    major: int
    minor: int
    patch: int
    pre_release: Optional[str] = None

    def __str__(self) -> str:
        ver = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            ver += f"-{self.pre_release}"
        return ver

    @classmethod
    def parse(cls, ver_str: str) -> SemVer:
        """Parses standard semver strings (e.g. '1.2.3-rc1')."""
        pre = None
        if "-" in ver_str:
            ver_str, pre = ver_str.split("-", 1)
        parts = [int(p) for p in ver_str.split(".")]
        while len(parts) < 3:
            parts.append(0)
        return cls(parts[0], parts[1], parts[2], pre)


@dataclass
class CapabilityHealth:
    """Tracks latency, availability, and error rates of registered capabilities."""

    is_available: bool = True
    latency_ms: float = 0.0
    error_rate: float = 0.0
    last_execution: str = ""
    usage_count: int = 0
    failure_count: int = 0


@dataclass
class CapabilityMetadata:
    """Unified metadata defining a registered capability control plane entry."""

    capability_id: str
    name: str
    type: CapabilityType
    version: str
    description: str
    author: str = "Nexus AI Core"
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    compatibilities: List[str] = field(default_factory=list)  # Supported API/Runtime versions
    is_deprecated: bool = False
    upgrade_path: Optional[str] = None  # Recommended upgrade version string
    health: CapabilityHealth = field(default_factory=CapabilityHealth)
    extra: Dict[str, Any] = field(default_factory=dict)
