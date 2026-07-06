"""Pydantic schemas and enums for the Plugin & Extension Framework."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginState(str, Enum):
    """Represents the lifecycle state of a registered plugin."""
    UNLOADED = "UNLOADED"
    LOADED = "LOADED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


class PluginManifest(BaseModel):
    """Describes metadata, capabilities, dependencies, permissions, and entry points of a plugin."""
    name: str
    version: str
    author: str
    description: str
    capabilities: List[str] = Field(default_factory=list)  # E.g. "Intelligence Module", "Model Provider"
    dependencies: Dict[str, str] = Field(default_factory=dict)  # plugin_name -> version constraint
    min_runtime_version: str = "1.0.0"
    permissions: List[str] = Field(default_factory=list)  # E.g. "network", "filesystem"
    entry_point: str  # Class path string (e.g. "sample_plugin.SamplePlugin")
    config_schema: Dict[str, Any] = Field(default_factory=dict)


class PluginInfo(BaseModel):
    """Tracks manifest data along with active state, health status, and error logs."""
    manifest: PluginManifest
    state: PluginState = PluginState.UNLOADED
    health_status: str = "healthy"  # "healthy", "degraded", "failing"
    error_message: Optional[str] = None
