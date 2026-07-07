"""Config manager coordinating environment profiles, feature flags, and validation checks."""

from __future__ import annotations

import os
import threading
from typing import Any, Dict, List, Optional

from backend.config.config_validator import ConfigValidator
from backend.config.config_watcher import ConfigWatcher
from backend.config.environment_loader import EnvironmentLoader
from backend.config.feature_flag_manager import FeatureFlagManager
from backend.config.models import AppConfig
from backend.config.secret_manager import SecretManager
from backend.config.workspace_config import WorkspaceConfig


class ConfigManager:
    """The central manager (facade) coordinating settings, flags, secrets, and watchers."""

    _instance: Optional["ConfigManager"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "ConfigManager":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config.json") -> None:
        if getattr(self, "_initialized", False):
            return
        self._lock = threading.RLock()
        self.config_path = config_path

        # 1. Load configuration from environment profile
        self._config = EnvironmentLoader.load_from_env()

        # 2. Instantiate sub-managers
        self.feature_flags = FeatureFlagManager(self._config.feature_flags)
        self.secrets = SecretManager()
        self.workspaces = WorkspaceConfig()

        # 3. Setup File Watcher for hot reload
        self._watcher = ConfigWatcher(config_path, self._handle_hot_reload)
        if os.path.exists(config_path):
            self._watcher.start()

        self._initialized = True

    def get_config(self) -> AppConfig:
        """Returns the current AppConfig settings."""
        with self._lock:
            return self._config

    def validate_config(self) -> List[str]:
        """Audits current settings for warning and errors."""
        with self._lock:
            return ConfigValidator.validate(self._config)

    def force_reload(self) -> None:
        """Forces checking config file changes and updates configuration."""
        self._watcher.force_check()

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Directly updates config variables thread-safely."""
        with self._lock:
            # Merge dictionary settings into current configuration
            current_dict = self._config.model_dump()
            self._merge_dict(current_dict, settings)
            self._config = AppConfig(**current_dict)

            # Update feature flags
            for k, v in self._config.feature_flags.items():
                self.feature_flags.set_flag(k, v)

    def _handle_hot_reload(self, new_data: Dict[str, Any]) -> None:
        self.update_settings(new_data)

    def _merge_dict(self, target: dict, source: dict) -> None:
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._merge_dict(target[k], v)
            else:
                target[k] = v

    def shutdown(self) -> None:
        """Shuts down active background watchers."""
        self._watcher.stop()
