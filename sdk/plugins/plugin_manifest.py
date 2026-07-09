"""Plugin manifest builder providing a fluent API to define plugin metadata."""

from __future__ import annotations

from typing import List, Optional

from sdk.plugins.models import PluginManifestModel, PluginPermission, PluginType


class PluginManifest:
    """Fluent builder for constructing a :class:`PluginManifestModel`.

    Example::

        manifest = (
            PluginManifest()
            .id("my_connector")
            .name("My Connector")
            .version("2.1.0")
            .author("Acme Corp")
            .description("Connects to external data sources.")
            .plugin_type(PluginType.CONNECTOR)
            .permission(PluginPermission.NETWORK)
            .permission(PluginPermission.PROVIDERS)
            .compatible_with(">=1.2.0")
            .entry_point("acme.my_connector.MyConnector")
            .build()
        )
    """

    def __init__(self) -> None:
        self._plugin_id: str = ""
        self._name: str = ""
        self._version: str = "1.0.0"
        self._author: str = ""
        self._description: str = ""
        self._plugin_type: PluginType = PluginType.MARKETPLACE_EXTENSION
        self._permissions: List[PluginPermission] = []
        self._dependencies: dict[str, str] = {}
        self._compatible_nexus_version: str = ">=1.0.0"
        self._entry_point: str = ""
        self._tags: List[str] = []

    def id(self, plugin_id: str) -> "PluginManifest":
        """Sets the unique plugin identifier.

        Args:
            plugin_id: Unique string key for the plugin.

        Returns:
            Self for method chaining.
        """
        self._plugin_id = plugin_id
        return self

    def name(self, name: str) -> "PluginManifest":
        """Sets the human-readable plugin name."""
        self._name = name
        return self

    def version(self, semver: str) -> "PluginManifest":
        """Sets the semantic version string."""
        self._version = semver
        return self

    def author(self, author: str) -> "PluginManifest":
        """Sets the author name or email."""
        self._author = author
        return self

    def description(self, desc: str) -> "PluginManifest":
        """Sets the human-readable description."""
        self._description = desc
        return self

    def plugin_type(self, ptype: PluginType) -> "PluginManifest":
        """Sets the plugin category type."""
        self._plugin_type = ptype
        return self

    def permission(self, perm: PluginPermission) -> "PluginManifest":
        """Adds a permission scope the plugin requires."""
        if perm not in self._permissions:
            self._permissions.append(perm)
        return self

    def dependency(self, package: str, constraint: str) -> "PluginManifest":
        """Declares an external package dependency."""
        self._dependencies[package] = constraint
        return self

    def compatible_with(self, nexus_version: str) -> "PluginManifest":
        """Sets the minimum compatible Nexus version constraint."""
        self._compatible_nexus_version = nexus_version
        return self

    def entry_point(self, module_path: str) -> "PluginManifest":
        """Sets the dotted Python entry-point module path."""
        self._entry_point = module_path
        return self

    def tag(self, label: str) -> "PluginManifest":
        """Adds a discovery tag to the plugin."""
        self._tags.append(label)
        return self

    def build(self) -> PluginManifestModel:
        """Validates fields and returns an immutable :class:`PluginManifestModel`.

        Returns:
            Validated manifest model.

        Raises:
            ValueError: If plugin_id or name is missing.
        """
        if not self._plugin_id.strip():
            raise ValueError("Plugin 'plugin_id' is required.")
        if not self._name.strip():
            raise ValueError("Plugin 'name' is required.")

        return PluginManifestModel(
            plugin_id=self._plugin_id,
            name=self._name,
            version=self._version,
            author=self._author,
            description=self._description,
            plugin_type=self._plugin_type,
            permissions=list(self._permissions),
            dependencies=dict(self._dependencies),
            compatible_nexus_version=self._compatible_nexus_version,
            entry_point=self._entry_point,
            tags=list(self._tags),
        )
