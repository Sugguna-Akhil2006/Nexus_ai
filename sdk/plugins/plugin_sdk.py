"""Abstract base class defining the Nexus Plugin SDK contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from sdk.plugins.models import PluginManifestModel


class NexusPlugin(ABC):
    """Abstract base every Nexus plugin must inherit from.

    Third-party developers subclass :class:`NexusPlugin` and implement the
    lifecycle hooks.  The SDK guarantees these hooks are called in order:

    1. :meth:`on_load`   – Plugin module imported, resources allocated.
    2. :meth:`on_enable` – Plugin activated and registered with the runtime.
    3. :meth:`on_disable`– Plugin deactivated; should release transient resources.
    4. :meth:`on_update` – New version installed while the plugin is running.
    5. :meth:`on_remove` – Plugin uninstalled; must free all resources.

    Example::

        class MyPlugin(NexusPlugin):
            @property
            def manifest(self) -> PluginManifestModel:
                return PluginManifest().id("my_plugin").name("My Plugin").build()

            def on_load(self) -> None:
                self._db = connect()

            def on_enable(self) -> None:
                register_routes(self)

            def on_disable(self) -> None:
                pass

            def on_update(self, new_version: str) -> None:
                pass

            def on_remove(self) -> None:
                self._db.close()
    """

    # ------------------------------------------------------------------
    # Required contract
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def manifest(self) -> PluginManifestModel:
        """Returns the plugin manifest describing this extension.

        Returns:
            Validated :class:`PluginManifestModel`.
        """

    @abstractmethod
    def on_load(self) -> None:
        """Called once when the plugin module is first imported."""

    @abstractmethod
    def on_enable(self) -> None:
        """Called when the plugin is activated."""

    @abstractmethod
    def on_disable(self) -> None:
        """Called when the plugin is deactivated."""

    @abstractmethod
    def on_update(self, new_version: str) -> None:
        """Called when the plugin is updated to a new version.

        Args:
            new_version: Semantic version string of the incoming update.
        """

    @abstractmethod
    def on_remove(self) -> None:
        """Called when the plugin is permanently uninstalled."""

    # ------------------------------------------------------------------
    # Optional overrides
    # ------------------------------------------------------------------

    def health_check(self) -> bool:
        """Returns True if the plugin is functioning correctly.

        Returns:
            Health status boolean.
        """
        return True

    def get_context(self) -> Dict[str, Any]:
        """Returns runtime context data the plugin exposes to the platform.

        Returns:
            Key/value context mapping.
        """
        return {}
