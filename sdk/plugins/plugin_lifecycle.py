"""Thread-safe plugin lifecycle manager handling install/enable/disable/update/remove."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from sdk.plugins.models import (
    PluginEvent,
    PluginEventType,
    PluginManifestModel,
    PluginRecord,
    PluginStatus,
)


class PluginLifecycle:
    """Manages the full lifecycle of all registered plugins in a thread-safe registry.

    The registry stores :class:`PluginRecord` objects keyed by plugin_id.
    All mutations are protected by a reentrant lock so that concurrent
    install / update / remove calls from the API layer are safe.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._registry: Dict[str, PluginRecord] = {}
        self._event_log: List[PluginEvent] = []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _emit(self, event_type: PluginEventType, plugin_id: str, **payload: object) -> None:
        """Records a lifecycle event in the internal log.

        Args:
            event_type: Category of lifecycle event.
            plugin_id: Target plugin identifier.
            **payload: Extra key/value data attached to the event.
        """
        event = PluginEvent(
            event_type=event_type,
            plugin_id=plugin_id,
            payload=dict(payload),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._event_log.append(event)

    # ------------------------------------------------------------------
    # Public lifecycle operations
    # ------------------------------------------------------------------

    def install(self, manifest: PluginManifestModel) -> PluginRecord:
        """Registers a plugin from its manifest.

        Args:
            manifest: Validated plugin manifest.

        Returns:
            New :class:`PluginRecord` with INSTALLED status.

        Raises:
            ValueError: If a plugin with the same ID is already registered.
        """
        with self._lock:
            if manifest.plugin_id in self._registry:
                raise ValueError(f"Plugin '{manifest.plugin_id}' is already installed.")
            record = PluginRecord(
                manifest=manifest,
                status=PluginStatus.INSTALLED,
                installed_at=datetime.now(timezone.utc).isoformat(),
            )
            self._registry[manifest.plugin_id] = record
            self._emit(PluginEventType.LOADED, manifest.plugin_id)
            return record

    def enable(self, plugin_id: str) -> PluginRecord:
        """Transitions a plugin from INSTALLED or DISABLED to ENABLED.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Updated :class:`PluginRecord`.

        Raises:
            KeyError: If the plugin is not found.
        """
        with self._lock:
            record = self._get_or_raise(plugin_id)
            record.status = PluginStatus.ENABLED
            record.error_message = None
            self._emit(PluginEventType.ENABLED, plugin_id)
            return record

    def disable(self, plugin_id: str) -> PluginRecord:
        """Transitions a plugin from ENABLED to DISABLED.

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Updated :class:`PluginRecord`.

        Raises:
            KeyError: If the plugin is not found.
        """
        with self._lock:
            record = self._get_or_raise(plugin_id)
            record.status = PluginStatus.DISABLED
            self._emit(PluginEventType.DISABLED, plugin_id)
            return record

    def update(self, plugin_id: str, new_version: str) -> PluginRecord:
        """Updates a plugin's version in place.

        Args:
            plugin_id: Plugin identifier.
            new_version: New semantic version string.

        Returns:
            Updated :class:`PluginRecord`.

        Raises:
            KeyError: If the plugin is not found.
        """
        with self._lock:
            record = self._get_or_raise(plugin_id)
            old_version = record.manifest.version
            record.manifest = record.manifest.model_copy(update={"version": new_version})
            record.status = PluginStatus.ENABLED
            self._emit(PluginEventType.UPDATED, plugin_id, old_version=old_version, new_version=new_version)
            return record

    def reload(self, plugin_id: str) -> PluginRecord:
        """Disables then re-enables a plugin (hot reload).

        Args:
            plugin_id: Plugin identifier.

        Returns:
            Updated :class:`PluginRecord`.
        """
        self.disable(plugin_id)
        return self.enable(plugin_id)

    def remove(self, plugin_id: str) -> None:
        """Permanently uninstalls a plugin from the registry.

        Args:
            plugin_id: Plugin identifier.

        Raises:
            KeyError: If the plugin is not found.
        """
        with self._lock:
            self._get_or_raise(plugin_id)
            del self._registry[plugin_id]
            self._emit(PluginEventType.REMOVED, plugin_id)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get(self, plugin_id: str) -> Optional[PluginRecord]:
        """Returns the plugin record for the given ID or None."""
        with self._lock:
            return self._registry.get(plugin_id)

    def list_plugins(self) -> List[PluginRecord]:
        """Returns all registered plugin records."""
        with self._lock:
            return list(self._registry.values())

    def events(self) -> List[PluginEvent]:
        """Returns all emitted lifecycle events."""
        return list(self._event_log)

    def _get_or_raise(self, plugin_id: str) -> PluginRecord:
        if plugin_id not in self._registry:
            raise KeyError(f"Plugin '{plugin_id}' not found in registry.")
        return self._registry[plugin_id]
