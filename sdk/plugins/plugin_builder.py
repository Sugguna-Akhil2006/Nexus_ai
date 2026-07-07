"""Plugin builder generating boilerplate source files for new plugin projects."""

from __future__ import annotations

import os
from typing import Dict

from sdk.plugins.models import PluginManifestModel, PluginType


class PluginBuilder:
    """Generates a complete plugin project directory from a manifest.

    The generated project includes:
    - ``__init__.py`` – package marker
    - ``plugin.py``   – skeleton :class:`NexusPlugin` subclass
    - ``models.py``   – empty configuration model
    - ``tests/test_<name>.py`` – starter test class

    Example::

        manifest = PluginManifest().id("my_plugin").name("My Plugin").build()
        files = PluginBuilder.generate_files(manifest)
        PluginBuilder.write_to_disk(files, base_dir="/workspace/plugins")
    """

    @staticmethod
    def generate_files(manifest: PluginManifestModel) -> Dict[str, str]:
        """Returns a mapping of relative file paths to their rendered content.

        Args:
            manifest: Validated plugin manifest.

        Returns:
            Dict mapping relative paths to string content.
        """
        pid = manifest.plugin_id
        class_name = "".join(word.capitalize() for word in pid.split("_"))

        init_content = f'"""{manifest.name} plugin package."""\n'

        plugin_content = f'''"""{manifest.name} plugin implementation."""

from __future__ import annotations

from sdk.plugins.models import PluginManifestModel, PluginType, PluginPermission
from sdk.plugins.plugin_manifest import PluginManifest
from sdk.plugins.plugin_sdk import NexusPlugin


class {class_name}(NexusPlugin):
    """{manifest.description or manifest.name} plugin."""

    @property
    def manifest(self) -> PluginManifestModel:
        """Returns the plugin manifest."""
        return (
            PluginManifest()
            .id("{pid}")
            .name("{manifest.name}")
            .version("{manifest.version}")
            .author("{manifest.author}")
            .description("{manifest.description}")
            .plugin_type(PluginType.{manifest.plugin_type.name})
            .entry_point("{pid}.plugin:{class_name}")
            .build()
        )

    def on_load(self) -> None:
        """Allocate resources on plugin load."""

    def on_enable(self) -> None:
        """Register hooks when plugin is activated."""

    def on_disable(self) -> None:
        """Release transient resources on deactivation."""

    def on_update(self, new_version: str) -> None:
        """Handle in-place version update."""

    def on_remove(self) -> None:
        """Free all resources on uninstall."""

    def health_check(self) -> bool:
        """Return plugin health status."""
        return True
'''

        models_content = f'''"""Configuration models for {manifest.name}."""

from pydantic import BaseModel


class {class_name}Config(BaseModel):
    """Configuration for the {manifest.name} plugin."""

    enabled: bool = True
'''

        test_content = f'''"""Unit tests for {manifest.name}."""

import unittest
from {pid}.plugin import {class_name}


class Test{class_name}(unittest.TestCase):
    """Verifies the {manifest.name} plugin lifecycle."""

    def setUp(self) -> None:
        self.plugin = {class_name}()

    def test_manifest(self) -> None:
        self.assertEqual(self.plugin.manifest.plugin_id, "{pid}")

    def test_health_check(self) -> None:
        self.assertTrue(self.plugin.health_check())

    def test_lifecycle(self) -> None:
        self.plugin.on_load()
        self.plugin.on_enable()
        self.plugin.on_disable()
        self.plugin.on_update("2.0.0")
        self.plugin.on_remove()
'''

        return {
            f"{pid}/__init__.py": init_content,
            f"{pid}/plugin.py": plugin_content.strip(),
            f"{pid}/models.py": models_content.strip(),
            f"{pid}/tests/__init__.py": '"""Tests package."""\n',
            f"{pid}/tests/test_{pid}.py": test_content.strip(),
        }

    @staticmethod
    def write_to_disk(files: Dict[str, str], base_dir: str) -> None:
        """Writes the generated plugin files to the filesystem.

        Args:
            files: Mapping of relative paths to content strings.
            base_dir: Absolute root directory to write under.
        """
        for rel_path, content in files.items():
            abs_path = os.path.join(base_dir, rel_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as fh:
                fh.write(content)
