"""Configuration Center managing general system settings and routing preferences."""

from __future__ import annotations

from typing import Any, Dict


class ConfigurationCenter:
    """Manages configurations for platform routing and failover timeouts."""

    def __init__(self) -> None:
        self._settings: Dict[str, Any] = {
            "default_timeout_seconds": 15.0,
            "max_retry_attempts": 3,
            "enable_fallback_routing": True,
            "alert_email": "admin@nexus.ai"
        }

    def get_setting(self, key: str) -> Any:
        return self._settings.get(key)

    def set_setting(self, key: str, value: Any) -> None:
        self._settings[key] = value

    def get_all_settings(self) -> Dict[str, Any]:
        return self._settings
