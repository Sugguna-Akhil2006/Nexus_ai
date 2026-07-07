"""Plugin Manager managing enable/disable states and installs for extension plugins."""

from __future__ import annotations

from typing import List, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType
from backend.studio.models import PluginStatus


class PluginManager:
    """Installs, removes, and toggles enable/disable status for plugins."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def list_plugins(self) -> List[PluginStatus]:
        """Lists metadata details of all plugins."""
        caps = self.registry.list_capabilities(CapabilityType.PLUGIN)
        status_list = []
        for c in caps:
            status_list.append(PluginStatus(
                plugin_id=c.capability_id,
                name=c.name,
                version=c.version,
                is_enabled=c.extra.get("is_enabled", True),
                description=c.description
            ))
        return status_list

    def install_plugin(self, meta: CapabilityMetadata) -> bool:
        """Registers a new plugin in the registry marketplace."""
        meta.type = CapabilityType.PLUGIN
        meta.extra["is_enabled"] = True
        self.registry.register_capability(meta)
        return True

    def remove_plugin(self, plugin_id: str) -> bool:
        """Uninstalls/removes a plugin by removing it from the cache registry database."""
        # SQLite remove proxy:
        conn = self.registry._db._get_connection()
        try:
            conn.execute("DELETE FROM registry_capabilities WHERE capability_id = ?", (plugin_id,))
            conn.commit()
            self.registry._capabilities.pop(plugin_id, None)
            return True
        except Exception:
            return False
        finally:
            conn.close()

    def set_enabled_status(self, plugin_id: str, enabled: bool) -> bool:
        """Toggles enable/disable status of a plugin."""
        cap = self.registry.get_capability(plugin_id)
        if not cap or cap.type != CapabilityType.PLUGIN:
            return False

        cap.extra["is_enabled"] = enabled
        self.registry.register_capability(cap)
        return True
