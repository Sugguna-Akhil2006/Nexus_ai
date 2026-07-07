"""Base abstract interfaces that all external plugins must inherit from."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from backend.plugins.plugin_context import PluginContext


class BasePlugin(ABC):
    """Core plugin template class specifying standard lifecycle callbacks."""

    def __init__(self, ctx: PluginContext) -> None:
        self.ctx = ctx

    def on_load(self) -> None:
        """Invoked when the plugin is first loaded into memory."""
        pass

    def on_enable(self) -> None:
        """Invoked when the plugin transition to enabled state."""
        pass

    def on_disable(self) -> None:
        """Invoked when the plugin transition to disabled state."""
        pass

    def on_unload(self) -> None:
        """Invoked when the plugin is uninstalled or unloaded."""
        pass

    def health_check(self) -> str:
        """Checks internal components health. Returns 'healthy', 'degraded', or 'failing'."""
        return "healthy"
