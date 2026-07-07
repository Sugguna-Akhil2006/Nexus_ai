"""PluginBuilder - scaffolding builder for ADK plugin extensions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PluginManifest:
    """Plugin package manifest describing the extension.

    Attributes:
        plugin_name: Unique plugin identifier.
        version: Semantic version string.
        author: Author name or email.
        description: Human-readable description.
        capabilities: List of capability tag strings.
        dependencies: Mapping of dependency names to version constraints.
        entry_point: Python module path of the plugin entry class.
    """

    plugin_name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    dependencies: Dict[str, str] = field(default_factory=dict)
    entry_point: str = ""


class PluginBuilder:
    """Fluent builder for scaffolding Nexus ADK plugin extensions.

    Example::

        manifest = (
            PluginBuilder()
            .name("github_plugin")
            .version("1.0.0")
            .author("Dev Team")
            .description("GitHub integration plugin")
            .capability("github_fetch")
            .dependency("requests", ">=2.28.0")
            .entry_point("plugins.github_plugin.GitHubPlugin")
            .build()
        )
    """

    def __init__(self) -> None:
        self._plugin_name: str = ""
        self._version: str = "1.0.0"
        self._author: str = ""
        self._description: str = ""
        self._capabilities: List[str] = []
        self._dependencies: Dict[str, str] = {}
        self._entry_point: str = ""

    def name(self, plugin_name: str) -> "PluginBuilder":
        """Sets the plugin name.

        Args:
            plugin_name: Unique plugin identifier.

        Returns:
            Self for method chaining.
        """
        self._plugin_name = plugin_name
        return self

    def version(self, semver: str) -> "PluginBuilder":
        """Sets the plugin semantic version.

        Args:
            semver: Semantic version string.

        Returns:
            Self for method chaining.
        """
        self._version = semver
        return self

    def author(self, author_name: str) -> "PluginBuilder":
        """Sets the plugin author.

        Args:
            author_name: Author name or email string.

        Returns:
            Self for method chaining.
        """
        self._author = author_name
        return self

    def description(self, desc: str) -> "PluginBuilder":
        """Sets the plugin description.

        Args:
            desc: Human-readable description.

        Returns:
            Self for method chaining.
        """
        self._description = desc
        return self

    def capability(self, cap: str) -> "PluginBuilder":
        """Adds a capability tag.

        Args:
            cap: Capability tag string.

        Returns:
            Self for method chaining.
        """
        self._capabilities.append(cap)
        return self

    def dependency(self, package: str, version_constraint: str) -> "PluginBuilder":
        """Adds a package dependency.

        Args:
            package: Package name.
            version_constraint: Version constraint string (e.g. ``">=2.28.0"``).

        Returns:
            Self for method chaining.
        """
        self._dependencies[package] = version_constraint
        return self

    def entry_point(self, module_path: str) -> "PluginBuilder":
        """Sets the Python entry point module path.

        Args:
            module_path: Dotted module path (e.g. ``"plugins.my_plugin.MyPlugin"``).

        Returns:
            Self for method chaining.
        """
        self._entry_point = module_path
        return self

    def build(self) -> PluginManifest:
        """Validates and constructs the PluginManifest.

        Returns:
            PluginManifest instance.

        Raises:
            ValueError: If the plugin name is empty.
        """
        if not self._plugin_name.strip():
            raise ValueError("Plugin name is required.")

        return PluginManifest(
            plugin_name=self._plugin_name,
            version=self._version,
            author=self._author,
            description=self._description,
            capabilities=list(self._capabilities),
            dependencies=dict(self._dependencies),
            entry_point=self._entry_point,
        )

    def scaffold_files(self) -> Dict[str, str]:
        """Generates starter source file contents for the plugin.

        Returns:
            Dictionary mapping relative file paths to their content strings.
        """
        manifest = self.build()
        plugin_class = "".join(w.capitalize() for w in manifest.plugin_name.split("_"))

        main_file = f'''"""Auto-scaffolded plugin: {manifest.plugin_name}."""

from backend.sdk.sdk import SDKBase, SDKManifest, ExtensionType


class {plugin_class}(SDKBase):
    """Plugin: {manifest.description}"""

    @property
    def manifest(self) -> SDKManifest:
        return SDKManifest(
            extension_name="{manifest.plugin_name}",
            extension_type=ExtensionType.PLUGIN,
            sdk_version="1.0.0",
            runtime_version="1.0.0",
            author="{manifest.author}",
            license="MIT",
            capabilities={manifest.capabilities!r},
        )

    def initialize(self) -> None:
        pass

    def validate(self) -> None:
        pass

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health_check(self) -> bool:
        return True
'''
        return {
            f"{manifest.plugin_name}.py": main_file.strip(),
        }
