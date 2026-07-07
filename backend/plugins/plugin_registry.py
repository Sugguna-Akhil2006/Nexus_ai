"""Thread-safe registry stashing active plugin mappings in-memory."""

import threading
from typing import Dict, List, Optional, Any
from backend.plugins.models import PluginInfo
from backend.plugins.plugin_api import BasePlugin


class PluginRegistry:
    """Thread-safe storage registry mapping names to info and loaded instances."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._plugin_info_map: Dict[str, PluginInfo] = {}
        self._plugin_instance_map: Dict[str, BasePlugin] = {}

    def register_plugin(self, name: str, info: PluginInfo, instance: BasePlugin) -> None:
        """Registers a plugin name mapping thread-safely."""
        with self._lock:
            self._plugin_info_map[name] = info
            self._plugin_instance_map[name] = instance

    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """Fetches manifest info metadata for a plugin."""
        with self._lock:
            return self._plugin_info_map.get(name)

    def get_plugin_instance(self, name: str) -> Optional[BasePlugin]:
        """Fetches the instantiated active class instance."""
        with self._lock:
            return self._plugin_instance_map.get(name)

    def list_plugins(self) -> List[PluginInfo]:
        """Lists metadata records of all registered plugins."""
        with self._lock:
            return list(self._plugin_info_map.values())

    def unregister_plugin(self, name: str) -> None:
        """Removes a plugin registration."""
        with self._lock:
            self._plugin_info_map.pop(name, None)
            self._plugin_instance_map.pop(name, None)
