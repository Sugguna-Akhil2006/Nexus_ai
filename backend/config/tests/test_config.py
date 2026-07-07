"""Unit tests validating Configuration Management & Environment Profiles."""

from __future__ import annotations

import json
import os
import unittest

from backend.config.config_exporter import ConfigExporter
from backend.config.config_manager import ConfigManager
from backend.config.config_validator import ConfigValidator
from backend.config.environment_loader import EnvironmentLoader
from backend.config.feature_flag_manager import FeatureFlagManager
from backend.config.models import AppConfig, EnvironmentType
from backend.config.secret_manager import SecretManager
from backend.config.workspace_config import WorkspaceConfig


class TestEnvironmentLoader(unittest.TestCase):
    """Verifies env variable mapping to config models."""

    def test_defaults(self) -> None:
        config = EnvironmentLoader.load_from_env()
        self.assertEqual(config.server.host, "0.0.0.0")
        self.assertEqual(config.server.port, 8000)
        self.assertEqual(config.environment, EnvironmentType.DEVELOPMENT)

    def test_env_profile_selection(self) -> None:
        os.environ["NEXUS_ENV"] = "production"
        os.environ["PORT"] = "9000"
        try:
            config = EnvironmentLoader.load_from_env()
            self.assertEqual(config.environment, EnvironmentType.PRODUCTION)
            self.assertEqual(config.server.port, 9000)
        finally:
            os.environ.pop("NEXUS_ENV", None)
            os.environ.pop("PORT", None)


class TestFeatureFlagManager(unittest.TestCase):
    """Verifies feature flag switches."""

    def test_flags(self) -> None:
        ff = FeatureFlagManager({"experimental_composition": False})
        self.assertFalse(ff.is_enabled("experimental_composition"))

        ff.set_flag("experimental_composition", True)
        self.assertTrue(ff.is_enabled("experimental_composition"))


class TestSecretManager(unittest.TestCase):
    """Verifies masking rules and rotation hook callbacks."""

    def test_masking(self) -> None:
        self.assertEqual(SecretManager.mask_secret("sk-1234567890abcdef"), "sk-...cdef")
        self.assertEqual(SecretManager.mask_secret("short"), "******")
        self.assertEqual(SecretManager.mask_secret(""), "")

    def test_rotation_hooks(self) -> None:
        sm = SecretManager()
        sm.register_rotation_hook("temp_key", lambda: "rotated_val")
        self.assertEqual(sm.get_secret("temp_key"), "rotated_val")


class TestConfigValidator(unittest.TestCase):
    """Verifies configuration constraints and validations."""

    def test_invalid_port(self) -> None:
        config = EnvironmentLoader.load_from_env()
        config.server.port = 80  # Protected, invalid port range
        errors = ConfigValidator.validate(config)
        self.assertTrue(any("port" in err for err in errors))


class TestConfigWatcherAndHotReload(unittest.TestCase):
    """Verifies in-memory config updates and file reloader callbacks."""

    def test_manual_settings_update(self) -> None:
        # Create manager in memory
        manager = ConfigManager()
        manager.update_settings({"server": {"port": 8888}})

        config = manager.get_config()
        self.assertEqual(config.server.port, 8888)

    def test_export_formats(self) -> None:
        config = EnvironmentLoader.load_from_env()

        json_out = ConfigExporter.export_json(config)
        self.assertIn("environment", json_out)

        yaml_out = ConfigExporter.export_yaml(config)
        self.assertIn("environment:", yaml_out)

        toml_out = ConfigExporter.export_toml(config)
        self.assertIn("environment = ", toml_out)
        self.assertIn("[server]", toml_out)
