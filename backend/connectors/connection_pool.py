"""Connection Pool managing reuse of active connector instances."""

from __future__ import annotations

import threading
from typing import Dict, Optional

from backend.connectors.base_connector import BaseConnector
from backend.connectors.connector_registry import ConnectorRegistry
from backend.connectors.models import ConnectorConfig


class ConnectionPool:
    """Manages active connector objects to avoid reconnection overheads."""

    def __init__(self, registry: Optional[ConnectorRegistry] = None) -> None:
        self.registry = registry or ConnectorRegistry()
        self._pool: Dict[str, BaseConnector] = {}
        self._lock = threading.Lock()

    def get_connection(self, config: ConnectorConfig) -> BaseConnector:
        """Retrieves or instantiates a connector driver object."""
        with self._lock:
            if config.connector_id in self._pool:
                return self._pool[config.connector_id]

            driver_cls = self.registry.get_driver_class(config.connector_type)
            if not driver_cls:
                raise ValueError(f"Unknown connector driver type: '{config.connector_type}'.")

            conn = driver_cls(config)
            self._pool[config.connector_id] = conn
            return conn

    def remove_connection(self, connector_id: str) -> None:
        with self._lock:
            self._pool.pop(connector_id, None)

    def clear(self) -> None:
        with self._lock:
            self._pool.clear()
