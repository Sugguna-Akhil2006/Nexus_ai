"""Central facade coordinator managing loading, lifecycle transitions, and sandbox executions."""

import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from backend.runtime.event import Event, EventType, EventBus
from backend.plugins.models import PluginManifest, PluginInfo, PluginState
from backend.plugins.plugin_manifest import PluginManifestParser
from backend.plugins.plugin_validator import PluginValidator
from backend.plugins.dependency_resolver import DependencyResolver
from backend.plugins.plugin_loader import PluginLoader
from backend.plugins.plugin_registry import PluginRegistry
from backend.plugins.plugin_lifecycle import PluginLifecycleManager
from backend.plugins.sandbox import PluginSandbox
from backend.plugins.plugin_context import PluginContext


class PluginManager:
    """Core platform interface discovering plugins, invoking hooks, and verifying execution boundaries."""

    def __init__(self, platform_version: str = "1.0.0", db_path: str = "nexus_ai.db") -> None:
        self.platform_version = platform_version
        self.registry = PluginRegistry()
        self.validator = PluginValidator(platform_version)
        self.resolver = DependencyResolver()
        self.loader = PluginLoader()
        self.lifecycle = PluginLifecycleManager()
        self.sandbox = PluginSandbox()
        self.event_bus = EventBus()

    def discover_and_load_plugins(self, root_dir: str, workspace_id: str) -> None:
        """Scans directories for manifest.json configurations, loading entries topologically."""
        if not os.path.exists(root_dir):
            return

        manifests: Dict[str, PluginManifest] = {}
        dirs_map: Dict[str, str] = {}

        # 1. Discover all manifests in subdirectories
        for entry in os.scandir(root_dir):
            if entry.is_dir():
                manifest_path = os.path.join(entry.path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        manifest = PluginManifestParser.parse_file(manifest_path)
                        self.validator.validate_manifest(manifest)
                        manifests[manifest.name] = manifest
                        dirs_map[manifest.name] = entry.path
                    except Exception as e:
                        # Publish failed event for validation crashes
                        self._publish_failed_event(entry.name, f"Manifest validation error: {str(e)}")

        # 2. Resolve dependency load order
        try:
            load_order = self.resolver.resolve_load_order(manifests)
        except Exception as e:
            self._publish_failed_event("dependency_resolver", f"Topological resolve crashed: {str(e)}")
            return

        # 3. Load and register plugins in order
        for name in load_order:
            manifest = manifests[name]
            plugin_dir = dirs_map[name]
            info = PluginInfo(manifest=manifest)
            
            try:
                # Load entry class type
                plugin_class = self.loader.load_plugin_class(manifest.entry_point, plugin_dir)
                
                # Create context and instantiate
                ctx = PluginContext(name, workspace_id)
                instance = plugin_class(ctx)
                
                # Trigger lifecycle load
                self.lifecycle.load(info, instance)
                self.registry.register_plugin(name, info, instance)

                # Emit load telemetry event
                self.event_bus.publish(Event(
                    event_type=EventType.CUSTOM_EVENT,
                    source="PluginManager",
                    payload={
                        "event": "plugin.loaded",
                        "plugin_name": name,
                        "version": manifest.version,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ))
            except Exception as e:
                info.state = PluginState.FAILED
                info.health_status = "failing"
                info.error_message = str(e)
                self._publish_failed_event(name, f"Load initialization crashed: {str(e)}")

    def enable_plugin(self, name: str) -> None:
        """Transitions state to ENABLED and fires enabling lifecycle callbacks."""
        info = self.registry.get_plugin_info(name)
        instance = self.registry.get_plugin_instance(name)
        if not info or not instance:
            raise ValueError(f"Plugin '{name}' is not registered.")
        
        try:
            self.lifecycle.enable(info, instance)
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="PluginManager",
                payload={
                    "event": "plugin.enabled",
                    "plugin_name": name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        except Exception as e:
            self._publish_failed_event(name, f"Enable failed: {str(e)}")

    def disable_plugin(self, name: str) -> None:
        """Transitions state to DISABLED and fires disabling lifecycle callbacks."""
        info = self.registry.get_plugin_info(name)
        instance = self.registry.get_plugin_instance(name)
        if not info or not instance:
            raise ValueError(f"Plugin '{name}' is not registered.")
        
        try:
            self.lifecycle.disable(info, instance)
            self.event_bus.publish(Event(
                event_type=EventType.CUSTOM_EVENT,
                source="PluginManager",
                payload={
                    "event": "plugin.disabled",
                    "plugin_name": name,
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        except Exception as e:
            self._publish_failed_event(name, f"Disable failed: {str(e)}")

    def execute_plugin_method(self, name: str, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """Safely runs a plugin method wrapped inside isolated sandbox handlers."""
        info = self.registry.get_plugin_info(name)
        instance = self.registry.get_plugin_instance(name)
        if not info or not instance:
            raise ValueError(f"Plugin '{name}' is not loaded.")
        if info.state != PluginState.ENABLED:
            raise RuntimeError(f"Cannot execute method: Plugin '{name}' is not ENABLED (Current state: {info.state}).")

        target_func = getattr(instance, method_name, None)
        if not target_func:
            raise AttributeError(f"Plugin '{name}' has no attribute/method '{method_name}'.")

        try:
            return self.sandbox.execute_safely(target_func, info.manifest.permissions, *args, **kwargs)
        except Exception as e:
            # Sync failing status on uncaught crashes
            info.state = PluginState.FAILED
            info.health_status = "failing"
            info.error_message = str(e)
            self._publish_failed_event(name, f"Execution failed in '{method_name}': {str(e)}")
            raise e

    def _publish_failed_event(self, name: str, reason: str) -> None:
        """Publishes standard event alerts for plugin failures."""
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="PluginManager",
            payload={
                "event": "plugin.failed",
                "plugin_name": name,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
