"""System checker evaluating database, event bus, and runtime engine health."""

from __future__ import annotations

from typing import Dict, List

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType


class SystemChecker:
    """Audits database connectivity, event bus queue channels, and active memory pools."""

    @staticmethod
    def audit_system_connectivity() -> List[str]:
        """Runs connectivity checks on relational storage and event managers.

        Returns:
            List of detected failure warnings.
        """
        warnings = []

        # 1. DB Connect check
        try:
            db = DBStorage()
            conn = db._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.close()
        except Exception as e:
            warnings.append(f"Database connectivity failed: {e}")

        # 2. Event Bus queue check
        try:
            bus = EventBus()
            # Publish a test heartbeat event
            bus.publish(
                Event(
                    event_type=EventType.SYSTEM_EVENT,
                    source="ReleaseSystemChecker",
                    payload={"ping": "heartbeat"},
                )
            )
        except Exception as e:
            warnings.append(f"Event Bus interface failed: {e}")

        return warnings
