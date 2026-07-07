"""Core Pydantic models for the Nexus Plugin SDK."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginType(str, Enum):
    """Supported plugin extension categories."""

    INTELLIGENCE_MODULE = "intelligence_module"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    PROVIDER = "provider"
    DASHBOARD_WIDGET = "dashboard_widget"
    CLI_COMMAND = "cli_command"
    MARKETPLACE_EXTENSION = "marketplace_extension"


class PluginPermission(str, Enum):
    """Declared permission scopes a plugin may request."""

    FILESYSTEM = "filesystem"
    NETWORK = "network"
    PROVIDERS = "providers"
    KNOWLEDGE_FABRIC = "knowledge_fabric"
    WORKSPACES = "workspaces"
    SANDBOX = "sandbox"
    ENVIRONMENT_VARIABLES = "environment_variables"


class PluginStatus(str, Enum):
    """Runtime lifecycle state of a registered plugin."""

    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class PluginEventType(str, Enum):
    """Plugin lifecycle event categories."""

    LOADED = "plugin.loaded"
    ENABLED = "plugin.enabled"
    DISABLED = "plugin.disabled"
    UPDATED = "plugin.updated"
    REMOVED = "plugin.removed"
    ERROR = "plugin.error"


class PluginManifestModel(BaseModel):
    """Standardised plugin manifest schema describing extension metadata."""

    plugin_id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    plugin_type: PluginType = PluginType.MARKETPLACE_EXTENSION
    permissions: List[PluginPermission] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    compatible_nexus_version: str = ">=1.0.0"
    entry_point: str = ""
    tags: List[str] = Field(default_factory=list)


class PluginRecord(BaseModel):
    """Runtime record of an installed plugin with its current status."""

    manifest: PluginManifestModel
    status: PluginStatus = PluginStatus.INSTALLED
    installed_at: str = ""
    error_message: Optional[str] = None


class PluginValidationResult(BaseModel):
    """Result from the plugin manifest and code validator."""

    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PluginEvent(BaseModel):
    """A lifecycle event emitted by the plugin system."""

    event_type: PluginEventType
    plugin_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


class PluginTestResult(BaseModel):
    """Outcome of running a plugin's test suite."""

    plugin_id: str
    passed: int = 0
    failed: int = 0
    errors: List[str] = Field(default_factory=list)
    success: bool = False
