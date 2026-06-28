from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import threading
from typing import Any, Dict, List, Optional
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import NexusException
from backend.runtime.logger import StructuredLogger


class PluginError(NexusException):
    """Base exception for all plugin-related errors."""
    pass


class PluginValidationError(PluginError):
    """Raised when validation of plugin manifests, dependencies, or entry points fails."""
    pass


class PluginDependencyError(PluginError):
    """Raised when there is a missing dependency or a circular dependency in plugins."""
    pass


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found in the registry."""
    pass


class PluginCapability(Enum):
    """Supported classifications of capabilities extended by plugins."""
    MODEL_PROVIDER = "MODEL_PROVIDER"
    STORAGE_PROVIDER = "STORAGE_PROVIDER"
    VECTOR_PROVIDER = "VECTOR_PROVIDER"
    OCR_PROVIDER = "OCR_PROVIDER"
    SEARCH_PROVIDER = "SEARCH_PROVIDER"
    TOOL_PROVIDER = "TOOL_PROVIDER"
    AUTH_PROVIDER = "AUTH_PROVIDER"
    UI_EXTENSION = "UI_EXTENSION"
    CUSTOM = "CUSTOM"


class PluginState(Enum):
    """Lifecycle states of registered plugins."""
    DISCOVERED = "DISCOVERED"
    LOADED = "LOADED"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"
    UNLOADED = "UNLOADED"


@dataclass(frozen=True)
class Plugin:
    """Immutable model encapsulating plugin identity and structural metadata.

    Attributes:
        plugin_id: Unique identifier string for the plugin.
        name: Common name of the plugin.
        version: Version string (e.g. 1.0.0).
        author: Author descriptor.
        description: Textual description.
        license: License information.
        runtime_version: Compatibility rule requirements (e.g. >=1.0.0).
        dependencies: Dependencies (IDs) this plugin requires.
        capabilities: Extended capability interfaces.
        entry_point: Code execution entry point identifier.
        metadata: Extra metadata details.
    """
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    license: str
    runtime_version: str
    dependencies: List[str] = field(default_factory=list)
    capabilities: List[PluginCapability] = field(default_factory=list)
    entry_point: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PluginManifest:
    """Configuration schema descriptor loaded from plugin manifests.

    Attributes:
        metadata: Manifest meta definitions.
        dependencies: Dependencies requested.
        compatibility: Version compatibility boundaries.
        permissions: Authorization permissions (placeholder).
        configuration_schema: Dictionary defining expected options.
    """
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    compatibility: Dict[str, str] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    configuration_schema: Dict[str, Any] = field(default_factory=dict)


class PluginBase(ABC):
    """Abstract interface defining basic hook parameters for runtime extension."""

    def initialize(self) -> None:
        """Invoked when loading a plugin into the runtime memory registry."""
        pass

    def start(self) -> None:
        """Invoked when enabling the plugin workflow."""
        pass

    def stop(self) -> None:
        """Invoked when disabling the plugin workflow."""
        pass

    def shutdown(self) -> None:
        """Invoked when unloading the plugin from runtime registries."""
        pass

    def health_check(self) -> bool:
        """Verifies active connectivity health metrics.

        Returns:
            bool: True if healthy, False otherwise.
        """
        return True

    def configuration_schema(self) -> Dict[str, Any]:
        """Provides validation specifications for variables configuration.

        Returns:
            Dict[str, Any]: Configuration JSON schema payload.
        """
        return {}


class PluginManager:
    """Thread-safe Singleton managing discover, load, lifecycle hooks, and dependencies."""
    _instance: Optional["PluginManager"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "PluginManager":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, plugins_dir: Optional[str] = None) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self.logger = StructuredLogger()
            self.event_bus = EventBus()
            self._plugins_dir = plugins_dir or os.path.join(os.getcwd(), "plugins")
            self._plugins: Dict[str, Plugin] = {}
            self._instances: Dict[str, PluginBase] = {}
            self._states: Dict[str, PluginState] = {}
            self._lock: threading.RLock = threading.RLock()
            self._runtime_version = "1.0.0"
            self._initialized = True

    def set_plugins_dir(self, directory: str) -> None:
        """Changes target discovery scan folder.

        Args:
            directory: Directory path string.
        """
        with self._lock:
            self._plugins_dir = directory

    def register(self, plugin: Plugin, instance: Optional[PluginBase] = None) -> None:
        """Registers plugin details thread-safely.

        Args:
            plugin: Immutable Plugin metadata.
            instance: Active PluginBase code instance.

        Raises:
            PluginValidationError: If duplicate ID exists or verification checks fail.
        """
        if not plugin or not plugin.plugin_id or not str(plugin.plugin_id).strip():
            raise PluginValidationError("Invalid plugin entry point ID.")

        with self._lock:
            if plugin.plugin_id in self._plugins:
                raise PluginValidationError(
                    f"Plugin '{plugin.plugin_id}' is already registered in registry."
                )

            # Validate compatible version bounds
            if not self._is_compatible(plugin.runtime_version, self._runtime_version):
                raise PluginValidationError(
                    f"Incompatible runtime version: Plugin requires '{plugin.runtime_version}', but current is '{self._runtime_version}'."
                )

            self._plugins[plugin.plugin_id] = plugin
            self._states[plugin.plugin_id] = PluginState.DISCOVERED
            if instance:
                self._instances[plugin.plugin_id] = instance

        self._publish_event("plugin.discovered", plugin.plugin_id)
        self.logger.info(f"Plugin registered successfully. ID: {plugin.plugin_id}")

    def discover(self) -> List[Plugin]:
        """Scans plugins directory manifest schemas to discover and register components.

        Returns:
            List[Plugin]: List of discovered Plugins.
        """
        discovered_list = []
        if not os.path.exists(self._plugins_dir):
            return discovered_list

        self.logger.info(f"Starting plugins discovery in: {self._plugins_dir}")

        for item in os.listdir(self._plugins_dir):
            item_path = os.path.join(self._plugins_dir, item)
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, "r") as f:
                            data = json.load(f)

                        capabilities = [
                            PluginCapability(c) for c in data.get("capabilities", [])
                        ]

                        plugin = Plugin(
                            plugin_id=data["plugin_id"],
                            name=data["name"],
                            version=data["version"],
                            author=data.get("author", ""),
                            description=data.get("description", ""),
                            license=data.get("license", ""),
                            runtime_version=data.get("runtime_version", "*"),
                            dependencies=data.get("dependencies", []),
                            capabilities=capabilities,
                            entry_point=data.get("entry_point", ""),
                            metadata=data.get("metadata", {})
                        )

                        self.register(plugin)
                        discovered_list.append(plugin)
                    except Exception as e:
                        self.logger.error(f"Failed to load manifest '{manifest_path}': {e}")

        return discovered_list

    def load(self, plugin_id: str) -> None:
        """Initializes plugin and sets state to LOADED.

        Args:
            plugin_id: The ID of the plugin.

        Raises:
            PluginNotFoundError: If ID is not registered.
            PluginValidationError: If dependencies are missing.
        """
        with self._lock:
            plugin = self._plugins.get(plugin_id)
            if not plugin:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")

            # Validate dependencies resolved
            for dep in plugin.dependencies:
                if dep not in self._states or self._states[dep] not in (
                    PluginState.LOADED,
                    PluginState.ENABLED
                ):
                    raise PluginValidationError(
                        f"Failed to load plugin '{plugin_id}': Dependency '{dep}' is not loaded."
                    )

            instance = self._instances.get(plugin_id)
            if not instance:
                # If no instance passed during registration, instantiate a default placeholder class
                instance = DefaultPluginInstance()
                self._instances[plugin_id] = instance

            try:
                instance.initialize()
                self._states[plugin_id] = PluginState.LOADED
            except Exception as e:
                self._states[plugin_id] = PluginState.FAILED
                self._publish_event("plugin.failed", plugin_id, error=str(e))
                self.logger.error(f"Plugin load initialization crashed: {e}")
                raise PluginError(f"Initialization hook failed for '{plugin_id}': {e}") from e

        self._publish_event("plugin.loaded", plugin_id)
        self.logger.info(f"Plugin loaded. ID: {plugin_id}")

    def unload(self, plugin_id: str) -> None:
        """Shuts down and unregisters the plugin instance.

        Args:
            plugin_id: Unique plugin ID.
        """
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")

            # If enabled, stop first
            if self._states.get(plugin_id) == PluginState.ENABLED:
                self.disable(plugin_id)

            instance = self._instances.get(plugin_id)
            if instance:
                try:
                    instance.shutdown()
                except Exception as e:
                    self.logger.error(f"Shutdown error on '{plugin_id}': {e}")

            self._states[plugin_id] = PluginState.UNLOADED

        self._publish_event("plugin.unloaded", plugin_id)
        self.logger.info(f"Plugin unloaded. ID: {plugin_id}")

    def enable(self, plugin_id: str) -> None:
        """Enables the plugin instance workflow.

        Args:
            plugin_id: The ID of the plugin.
        """
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")

            if self._states[plugin_id] == PluginState.DISCOVERED:
                self.load(plugin_id)

            instance = self._instances.get(plugin_id)
            if not instance:
                raise PluginError(f"Cannot enable plugin '{plugin_id}': No instance registered.")

            try:
                instance.start()
                self._states[plugin_id] = PluginState.ENABLED
            except Exception as e:
                self._states[plugin_id] = PluginState.FAILED
                self._publish_event("plugin.failed", plugin_id, error=str(e))
                raise PluginError(f"Start hook failed for '{plugin_id}': {e}") from e

        self._publish_event("plugin.enabled", plugin_id)
        self.logger.info(f"Plugin enabled. ID: {plugin_id}")

    def disable(self, plugin_id: str) -> None:
        """Disables the plugin instance workflow.

        Args:
            plugin_id: The ID of the plugin.
        """
        with self._lock:
            if plugin_id not in self._plugins:
                raise PluginNotFoundError(f"Plugin '{plugin_id}' not found.")

            if self._states[plugin_id] != PluginState.ENABLED:
                return

            instance = self._instances.get(plugin_id)
            if instance:
                try:
                    instance.stop()
                except Exception as e:
                    self.logger.error(f"Stop hook error on '{plugin_id}': {e}")

            self._states[plugin_id] = PluginState.DISABLED

        self._publish_event("plugin.disabled", plugin_id)
        self.logger.info(f"Plugin disabled. ID: {plugin_id}")

    def reload(self, plugin_id: str) -> None:
        """Unloads and reloads a plugin.

        Args:
            plugin_id: Unique plugin ID.
        """
        with self._lock:
            self.unload(plugin_id)
            self.load(plugin_id)

    def get(self, plugin_id: str) -> Optional[Plugin]:
        """Retrieves plugin description details.

        Args:
            plugin_id: Unique plugin ID.

        Returns:
            Optional[Plugin]: Plugin metadata if exists.
        """
        with self._lock:
            return self._plugins.get(plugin_id)

    def get_instance(self, plugin_id: str) -> Optional[PluginBase]:
        """Retrieves plugin code execution instance.

        Args:
            plugin_id: Unique plugin ID.

        Returns:
            Optional[PluginBase]: The plugin class instance.
        """
        with self._lock:
            return self._instances.get(plugin_id)

    def list_plugins(self) -> List[Plugin]:
        """Lists metadata of all discovered plugins.

        Returns:
            List[Plugin]: List of Plugins.
        """
        with self._lock:
            return list(self._plugins.values())

    def list_capabilities(self) -> List[PluginCapability]:
        """Gathers list of capabilities registered by enabled plugins.

        Returns:
            List[PluginCapability]: Combined registered capabilities list.
        """
        caps = set()
        with self._lock:
            for pid, plugin in self._plugins.items():
                if self._states.get(pid) == PluginState.ENABLED:
                    caps.update(plugin.capabilities)
        return list(caps)

    def resolve_dependencies(self) -> List[str]:
        """Validates dependency paths and outputs deterministically sorted load order list.

        Returns:
            List[str]: Deterministic load ordering sequence.

        Raises:
            PluginDependencyError: On cycle loops or missing dependencies.
        """
        with self._lock:
            in_degree = {pid: 0 for pid in self._plugins}
            adj = {pid: [] for pid in self._plugins}

            for pid, plugin in self._plugins.items():
                for dep in plugin.dependencies:
                    if dep not in self._plugins:
                        raise PluginDependencyError(
                            f"Missing dependency: Plugin '{pid}' depends on unregistered plugin '{dep}'."
                        )
                    adj[dep].append(pid)
                    in_degree[pid] += 1

            queue = [pid for pid in self._plugins if in_degree[pid] == 0]
            queue.sort()  # deterministic start

            order = []
            while queue:
                curr = queue.pop(0)
                order.append(curr)
                for neighbor in adj[curr]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
                        queue.sort()

            if len(order) < len(self._plugins):
                raise PluginDependencyError("Circular dependency detected among plugins.")

            return order

    def _is_compatible(self, required: str, current: str) -> bool:
        if not required or required == "*":
            return True
        if required.startswith(">="):
            req_ver = required[2:].strip()
            try:
                req_parts = [int(x) for x in req_ver.split(".")]
                cur_parts = [int(x) for x in current.split(".")]
                return cur_parts >= req_parts
            except ValueError:
                return False
        return required == current

    def _publish_event(self, event_name: str, plugin_id: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="PluginSystem",
            payload={"event_name": event_name, "plugin_id": plugin_id, **kwargs}
        )
        self.event_bus.publish(event)


class DefaultPluginInstance(PluginBase):
    """Fallback placeholder class for plugins that do not provide custom classes."""
    pass
