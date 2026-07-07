"""Isolated runtime context environment exposed to plugins."""

from typing import Dict, Any, Callable
from backend.runtime.event import Event, EventType, EventBus
from backend.runtime.logger import StructuredLogger


class PluginContext:
    """Approved interface wrapper preventing plugins from accessing database or shell environments."""

    def __init__(self, plugin_name: str, workspace_id: str) -> None:
        self.plugin_name = plugin_name
        self.workspace_id = workspace_id
        self.event_bus = EventBus()
        self.logger = StructuredLogger()
        self.metrics: Dict[str, Any] = {}

    def log(self, level: str, message: str) -> None:
        """Sends sandboxed logs to standard logging framework."""
        getattr(self.logger, level.lower(), self.logger.info)(f"[Plugin:{self.plugin_name}] {message}")

    def publish_event(self, event_type_name: str, payload: Dict[str, Any]) -> None:
        """Publishes custom events into the Event Bus."""
        # Force plugin identity on payload
        payload["plugin_source"] = self.plugin_name
        
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source=f"Plugin:{self.plugin_name}",
            payload=payload
        ))

    def subscribe_event(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribes to standard platform events."""
        self.event_bus.subscribe(event_type, handler)

    def record_metric(self, key: str, value: Any) -> None:
        """Records tracking metrics in context logs."""
        self.metrics[key] = value
