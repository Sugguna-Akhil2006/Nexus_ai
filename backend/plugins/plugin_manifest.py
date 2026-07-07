"""Utility for parsing and deserialising plugin manifest files."""

import json
from typing import Dict, Any
from backend.plugins.models import PluginManifest


class PluginManifestParser:
    """Deserializes dictionary and JSON configuration payloads into PluginManifest structures."""

    @classmethod
    def parse_dict(cls, data: Dict[str, Any]) -> PluginManifest:
        """Parses a dictionary matching the PluginManifest schema."""
        return PluginManifest(**data)

    @classmethod
    def parse_file(cls, filepath: str) -> PluginManifest:
        """Reads and deserializes a JSON manifest file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.parse_dict(data)
