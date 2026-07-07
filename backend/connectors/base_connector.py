"""Base Connector abstract class defining shared connection interface structures."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from backend.connectors.models import ConnectorConfig


class BaseConnector(ABC):
    """Abstract interface defining required contract methods for all external system drivers."""

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config

    @abstractmethod
    def validate_connection(self) -> bool:
        """Verifies if authentication credentials are valid and active."""
        pass

    @abstractmethod
    def perform_health_check(self) -> bool:
        """Pings endpoint to verify online availability status."""
        pass

    @abstractmethod
    def discover_metadata(self) -> Dict[str, Any]:
        """Queries connection schemas and object parameters."""
        pass

    @abstractmethod
    def sync_data(self, checkpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Performs incremental synchronization from checkpoint details."""
        pass
