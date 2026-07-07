"""Plugin event bus exposing lifecycle hooks to the platform and third-party listeners."""

from __future__ import annotations

import threading
from typing import Callable, Dict, List

from sdk.plugins.models import PluginEvent, PluginEventType


# Listener type: receives a PluginEvent and returns None
EventListener = Callable[[PluginEvent], None]


class PluginEvents:
    """Thread-safe event bus for plugin lifecycle notifications.

    Components register listeners for specific :class:`PluginEventType` values.
    When the lifecycle manager emits an event all matching listeners are called
    synchronously on the emitting thread.

    Example::

        bus = PluginEvents()

        @bus.on(PluginEventType.ENABLED)
        def handle_enable(event: PluginEvent) -> None:
            logger.info("Plugin enabled: %s", event.plugin_id)

        bus.emit(PluginEvent(event_type=PluginEventType.ENABLED, plugin_id="my_plugin"))
    """

    def __init__(self) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._listeners: Dict[PluginEventType, List[EventListener]] = {
            event_type: [] for event_type in PluginEventType
        }

    def on(self, event_type: PluginEventType) -> Callable[[EventListener], EventListener]:
        """Decorator that registers a listener for the specified event type.

        Args:
            event_type: Event category to subscribe to.

        Returns:
            Decorator function.
        """
        def decorator(fn: EventListener) -> EventListener:
            self.subscribe(event_type, fn)
            return fn
        return decorator

    def subscribe(self, event_type: PluginEventType, listener: EventListener) -> None:
        """Registers an event listener for a specific lifecycle event.

        Args:
            event_type: Event category to subscribe to.
            listener: Callable that accepts a :class:`PluginEvent`.
        """
        with self._lock:
            self._listeners[event_type].append(listener)

    def emit(self, event: PluginEvent) -> None:
        """Dispatches an event to all registered listeners for its type.

        Args:
            event: The lifecycle event to dispatch.
        """
        with self._lock:
            listeners = list(self._listeners.get(event.event_type, []))
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                # Never let a listener crash the emitting thread
                pass

    def clear(self, event_type: PluginEventType) -> None:
        """Removes all listeners for the specified event type.

        Args:
            event_type: Event category to clear.
        """
        with self._lock:
            self._listeners[event_type] = []
