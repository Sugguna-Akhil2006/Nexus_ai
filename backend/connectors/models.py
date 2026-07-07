"""Data schemas representing configurations, sync jobs, and health states for the Connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ConnectorConfig:
    """Configuration for an active external system connection."""

    connector_id: str
    workspace_id: str
    connector_type: str  # e.g. "github", "google_drive", "slack", "notion"
    name: str
    auth_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    last_sync_timestamp: Optional[str] = None


@dataclass
class SyncJob:
    """Representation of an incremental data synchronization job execution."""

    job_id: str
    connector_id: str
    status: str = "queued"  # queued, running, completed, failed
    records_processed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoint_state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConnectionHealth:
    """Availability status and check logs for a connector instance."""

    connector_id: str
    status: str = "healthy"  # healthy, degraded, disconnected
    latency_ms: float = 0.0
    last_check_timestamp: Optional[datetime] = None
    error_details: Optional[str] = None
