"""Core Pydantic data models for the Nexus AI Extension Marketplace."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PackageType(str, Enum):
    """Supported package types in the extension marketplace."""
    INTELLIGENCE_MODULE = "Intelligence Module"
    WORKFLOW = "Workflow"
    PLUGIN = "Plugin"
    CONNECTOR = "Connector"
    PROVIDER = "Provider"
    PROMPT_PACK = "Prompt Pack"
    DASHBOARD = "Dashboard"
    THEME = "Theme"
    CLI_EXTENSION = "CLI Extension"


class PackageMetadata(BaseModel):
    """Metadata schema representing package properties."""
    package_id: str
    version: str
    author: str
    license: str
    description: str
    compatibility: Dict[str, Any] = Field(default_factory=dict)  # e.g., {"min_core_version": "1.0.0", "os": ["windows", "linux"]}
    dependencies: Dict[str, str] = Field(default_factory=dict)  # e.g., {"another_package": ">=1.0.0"}
    release_notes: str = ""
    digital_signature: str = ""
    checksum: str = ""  # SHA-256 string for verifying package integrity


class Rating(BaseModel):
    """User rating representation for a package."""
    user_id: str
    score: int = Field(..., ge=1, le=5)
    comment: str = ""


class MarketplacePackage(BaseModel):
    """Represents a package listed in the remote marketplace catalog."""
    metadata: PackageMetadata
    package_type: PackageType
    publisher: str
    average_rating: float = 0.0
    ratings_count: int = 0
    downloads: int = 0
    ratings: List[Rating] = Field(default_factory=list)


class InstalledPackage(BaseModel):
    """Represents a package successfully installed locally."""
    metadata: PackageMetadata
    package_type: PackageType
    enabled: bool = True
    installed_at: str
    updated_at: Optional[str] = None
    backup_versions: List[str] = Field(default_factory=list)  # Backups stored locally for rollback
