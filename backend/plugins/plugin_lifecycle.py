"""Manages lifecycle transitions and safety checks for plugins."""

from backend.plugins.models import PluginInfo, PluginState
from backend.plugins.plugin_api import BasePlugin


class PluginLifecycleManager:
    """State-machine coordinator invoking load, enable, disable, and reload hooks."""

    def load(self, info: PluginInfo, instance: BasePlugin) -> None:
        """Transitions state to LOADED, executing load callback."""
        try:
            instance.on_load()
            info.state = PluginState.LOADED
            info.health_status = "healthy"
            info.error_message = None
        except Exception as e:
            info.state = PluginState.FAILED
            info.health_status = "failing"
            info.error_message = f"Load failed: {str(e)}"
            raise e

    def enable(self, info: PluginInfo, instance: BasePlugin) -> None:
        """Transitions state to ENABLED, executing enable callback."""
        if info.state not in (PluginState.LOADED, PluginState.DISABLED):
            raise ValueError(f"Cannot enable plugin in state: {info.state}")
        try:
            instance.on_enable()
            info.state = PluginState.ENABLED
            info.health_status = "healthy"
            info.error_message = None
        except Exception as e:
            info.state = PluginState.FAILED
            info.health_status = "failing"
            info.error_message = f"Enable failed: {str(e)}"
            raise e

    def disable(self, info: PluginInfo, instance: BasePlugin) -> None:
        """Transitions state to DISABLED, executing disable callback."""
        if info.state != PluginState.ENABLED:
            raise ValueError(f"Cannot disable plugin in state: {info.state}")
        try:
            instance.on_disable()
            info.state = PluginState.DISABLED
            info.health_status = "healthy"
            info.error_message = None
        except Exception as e:
            info.state = PluginState.FAILED
            info.health_status = "failing"
            info.error_message = f"Disable failed: {str(e)}"
            raise e

    def unload(self, info: PluginInfo, instance: BasePlugin) -> None:
        """Transitions state to UNLOADED, executing unload callback."""
        try:
            instance.on_unload()
            info.state = PluginState.UNLOADED
            info.health_status = "healthy"
            info.error_message = None
        except Exception as e:
            info.state = PluginState.FAILED
            info.health_status = "failing"
            info.error_message = f"Unload failed: {str(e)}"
            raise e

    def run_health_check(self, info: PluginInfo, instance: BasePlugin) -> str:
        """Queries the plugin subclass health report and syncs status fields."""
        if info.state == PluginState.FAILED:
            return "failing"
        try:
            status = instance.health_check()
            info.health_status = status
            return status
        except Exception as e:
            info.health_status = "failing"
            info.error_message = f"Health check crashed: {str(e)}"
            return "failing"
