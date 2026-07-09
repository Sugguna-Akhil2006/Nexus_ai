"""Tenant events handler notifying event bus of organization lifecycle updates."""

from __future__ import annotations

from backend.runtime.event import Event, EventBus, EventType


class TenantEvents:
    """Publishes tenant lifecycles events (created, suspended) to system bus queues."""

    def __init__(self) -> None:
        self.bus = EventBus()

    def publish_created(self, tenant_id: str, name: str) -> None:
        """Publishes SYSTEM_EVENT for tenant creation."""
        self.bus.publish(
            Event(
                event_type=EventType.SYSTEM_EVENT,
                source="TenantManagement",
                payload={"action": "tenant_created", "tenant_id": tenant_id, "name": name},
            )
        )

    def publish_suspended(self, tenant_id: str) -> None:
        """Publishes SYSTEM_EVENT for tenant suspension."""
        self.bus.publish(
            Event(
                event_type=EventType.SYSTEM_EVENT,
                source="TenantManagement",
                payload={"action": "tenant_suspended", "tenant_id": tenant_id},
            )
        )
DefinitionPath = "tenant_events.py"
