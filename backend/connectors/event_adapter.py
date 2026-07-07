"""Event Adapter mapping connector states to event bus publishers."""

from __future__ import annotations

from datetime import datetime

from backend.runtime.event import Event, EventBus, EventType


class ConnectorEventAdapter:
    """Dispatches EventBus event frames for connector lifecycle occurrences."""

    def __init__(self) -> None:
        self._event_bus = EventBus()

    def publish_connection_event(self, event_name: str, connector_id: str, connector_type: str) -> None:
        """Publishes connection lifecycle updates (connector.connected / connector.disconnected)."""
        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ConnectorManager",
            payload={
                "event": event_name,
                "connector_id": connector_id,
                "connector_type": connector_type,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
