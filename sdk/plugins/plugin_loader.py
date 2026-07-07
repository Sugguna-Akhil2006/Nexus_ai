"""Plugin loader resolving and importing plugin classes from their entry points."""

from __future__ import annotations

import importlib
from typing import Optional, Type

from sdk.plugins.models import PluginManifestModel
from sdk.plugins.plugin_sdk import NexusPlugin


class PluginLoader:
    """Dynamically imports :class:`NexusPlugin` subclasses from manifest entry points.

    The entry-point format is ``"dotted.module.path:ClassName"`` or
    ``"dotted.module.path.ClassName"`` (legacy dot-only notation).

    Example::

        loader = PluginLoader()
        plugin_cls = loader.load(manifest)
        instance = plugin_cls()
        instance.on_load()
    """

    @staticmethod
    def load(manifest: PluginManifestModel) -> Type[NexusPlugin]:
        """Imports and returns the plugin class referenced by the manifest entry point.

        Args:
            manifest: Plugin manifest containing the entry point string.

        Returns:
            The :class:`NexusPlugin` subclass.

        Raises:
            ImportError: If the module or class cannot be found.
            TypeError: If the imported class does not subclass :class:`NexusPlugin`.
        """
        entry = manifest.entry_point.strip()
        if not entry:
            raise ImportError(f"Plugin '{manifest.plugin_id}' has an empty entry_point.")

        # Support both "module:Class" and "module.Class" formats
        if ":" in entry:
            module_path, class_name = entry.rsplit(":", 1)
        else:
            module_path, class_name = entry.rsplit(".", 1)

        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as exc:
            raise ImportError(
                f"Cannot import plugin module '{module_path}' "
                f"for plugin '{manifest.plugin_id}': {exc}"
            ) from exc

        cls: Optional[Type[NexusPlugin]] = getattr(module, class_name, None)
        if cls is None:
            raise ImportError(
                f"Class '{class_name}' not found in module '{module_path}'."
            )
        if not (isinstance(cls, type) and issubclass(cls, NexusPlugin)):
            raise TypeError(
                f"'{class_name}' must subclass NexusPlugin "
                f"(got {type(cls).__name__})."
            )
        return cls
