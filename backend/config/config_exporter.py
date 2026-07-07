"""Config exporter converting Pydantic configuration settings to JSON, YAML, and TOML formats."""

from __future__ import annotations

import json
from typing import Any, Dict

from backend.config.models import AppConfig


class ConfigExporter:
    """Exports AppConfig instances to standard serialization targets without external dependencies."""

    @staticmethod
    def export_json(config: AppConfig) -> str:
        """Serializes settings to a JSON format."""
        return config.model_dump_json(indent=2)

    @classmethod
    def export_yaml(cls, config: AppConfig) -> str:
        """Serializes settings to a YAML format using a simple dict-to-yaml printer."""
        data = config.model_dump()
        return cls._to_yaml(data)

    @classmethod
    def export_toml(cls, config: AppConfig) -> str:
        """Serializes settings to a TOML format using a dict-to-toml printer."""
        data = config.model_dump()
        return cls._to_toml(data)

    @classmethod
    def _to_yaml(cls, data: Any, indent: int = 0) -> str:
        lines = []
        spacing = "  " * indent
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    lines.append(f"{spacing}{k}:")
                    lines.append(cls._to_yaml(v, indent + 1))
                else:
                    lines.append(f"{spacing}{k}: {cls._to_val_str(v)}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    lines.append(f"{spacing}-")
                    lines.append(cls._to_yaml(item, indent + 1))
                else:
                    lines.append(f"{spacing}- {cls._to_val_str(item)}")
        return "\n".join(lines)

    @classmethod
    def _to_toml(cls, data: Any, section_prefix: str = "") -> str:
        lines = []
        tables = []
        for k, v in data.items():
            if isinstance(v, dict):
                full_sect = f"{section_prefix}.{k}" if section_prefix else k
                tables.append(f"\n[{full_sect}]")
                tables.append(cls._to_toml(v, full_sect))
            elif isinstance(v, list):
                # TOML list format
                list_str = ", ".join(cls._to_val_str(item) for item in v)
                lines.append(f"{k} = [{list_str}]")
            else:
                lines.append(f"{k} = {cls._to_val_str(v)}")
        return "\n".join(lines) + "".join(tables)

    @staticmethod
    def _to_val_str(val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if val is None:
            return '""'
        # String escape quotes
        clean = str(val).replace('"', '\\"')
        return f'"{clean}"'
DefinitionPath = "config_exporter.py"
