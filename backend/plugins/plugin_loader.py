"""Discovers, imports, and resolves python classes via importlib dynamically."""

import os
import sys
import importlib
from typing import Type
from backend.plugins.plugin_api import BasePlugin


class PluginLoader:
    """Imports external python script libraries by extending sys.path dynamically."""

    def load_plugin_class(self, entry_point: str, plugin_dir: str) -> Type[BasePlugin]:
        """Dynamically imports and resolves the plugin class structure."""
        # Add plugin directory to system path temporarily so importlib can resolve it
        abs_plugin_dir = os.path.abspath(plugin_dir)
        if abs_plugin_dir not in sys.path:
            sys.path.insert(0, abs_plugin_dir)

        try:
            if "." not in entry_point:
                raise ImportError(f"Entry point '{entry_point}' must specify a ModuleName.ClassName format.")
            
            module_name, class_name = entry_point.rsplit(".", 1)
            
            # Load the module
            module = importlib.import_module(module_name)
            # Fetch the class
            plugin_class = getattr(module, class_name)
            
            if not issubclass(plugin_class, BasePlugin):
                raise TypeError(f"Loaded entry class '{class_name}' must inherit from BasePlugin.")
                
            return plugin_class
        except Exception as e:
            raise ImportError(f"Failed to dynamically import entry point '{entry_point}': {str(e)}") from e
