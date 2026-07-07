"""Example connector plugin demonstrating the Nexus Plugin SDK contract."""

from __future__ import annotations

from sdk.plugins.models import PluginManifestModel, PluginPermission, PluginType
from sdk.plugins.plugin_manifest import PluginManifest
from sdk.plugins.plugin_sdk import NexusPlugin


class WeatherConnector(NexusPlugin):
    """Sample connector plugin that fetches weather data from a public API.

    This example demonstrates:
    - Manifest construction via the fluent builder.
    - Declaring NETWORK permission.
    - Implementing all required lifecycle hooks.
    """

    @property
    def manifest(self) -> PluginManifestModel:
        """Returns the WeatherConnector manifest."""
        return (
            PluginManifest()
            .id("weather_connector")
            .name("Weather Connector")
            .version("1.0.0")
            .author("Nexus Team")
            .description("Fetches current weather conditions from a REST endpoint.")
            .plugin_type(PluginType.CONNECTOR)
            .permission(PluginPermission.NETWORK)
            .compatible_with(">=1.0.0")
            .entry_point("sdk.plugins.examples.weather_connector:WeatherConnector")
            .tag("weather")
            .tag("connector")
            .build()
        )

    def on_load(self) -> None:
        """Initialise internal state."""
        self._cache: dict[str, object] = {}

    def on_enable(self) -> None:
        """Plugin activated – ready to serve requests."""

    def on_disable(self) -> None:
        """Plugin deactivated – flush cache."""
        self._cache.clear()

    def on_update(self, new_version: str) -> None:
        """Handle update to *new_version* gracefully."""

    def on_remove(self) -> None:
        """Release all resources."""
        self._cache.clear()

    def health_check(self) -> bool:
        """Always healthy in this example."""
        return True
