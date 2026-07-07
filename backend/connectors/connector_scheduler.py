"""Connector Scheduler managing recurring execution checks."""

from __future__ import annotations

from typing import Dict, Optional

from backend.connectors.models import ConnectorConfig
from backend.connectors.sync_engine import SyncEngine


class ConnectorScheduler:
    """Manages scheduled background synchronization loops."""

    def __init__(self, sync_engine: Optional[SyncEngine] = None) -> None:
        self.sync_engine = sync_engine or SyncEngine()
        self._schedules: Dict[str, int] = {}  # connector_id -> interval_seconds

    def schedule_connector(self, connector_id: str, interval_seconds: int) -> None:
        self._schedules[connector_id] = interval_seconds

    def unschedule_connector(self, connector_id: str) -> None:
        self._schedules.pop(connector_id, None)

    def trigger_scheduled_run(self, config: ConnectorConfig) -> bool:
        """Evaluates scheduling interval and triggers sync."""
        if config.connector_id in self._schedules:
            self.sync_engine.trigger_sync(config)
            return True
        return False
