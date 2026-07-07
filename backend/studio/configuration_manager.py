"""Configuration Manager compiling configuration bundles and format exports."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from backend.registry.capability_registry import CapabilityRegistry


class ConfigurationManager:
    """Manages active platform configuration state parameters and export formats."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def get_configuration_bundle(self) -> Dict[str, Any]:
        """Gathers capabilities, workspaces, and db settings into a single dict."""
        caps = self.registry.list_capabilities()
        
        bundle = {
            "version": "1.0.0",
            "exporter": "Nexus Studio Exporter",
            "capabilities": [
                {
                    "id": c.capability_id,
                    "name": c.name,
                    "type": c.type.value,
                    "version": c.version
                } for c in caps
            ]
        }
        return bundle

    def export_as(self, format_name: str) -> str:
        """Exports the active configuration bundle as JSON, Markdown or HTML."""
        bundle = self.get_configuration_bundle()
        fmt = format_name.lower()

        if fmt == "json":
            return json.dumps(bundle, indent=2)
        
        elif fmt == "markdown":
            lines = ["# Nexus AI Configuration Bundle", ""]
            lines.append(f"- **Exporter**: {bundle['exporter']}")
            lines.append(f"- **Version**: {bundle['version']}")
            lines.append("")
            lines.append("## Registered Capabilities")
            lines.append("| Capability ID | Name | Type | Version |")
            lines.append("| --- | --- | --- | --- |")
            for c in bundle["capabilities"]:
                lines.append(f"| {c['id']} | {c['name']} | {c['type']} | {c['version']} |")
            return "\n".join(lines)

        elif fmt == "html":
            rows = ""
            for c in bundle["capabilities"]:
                rows += f"<tr><td>{c['id']}</td><td>{c['name']}</td><td>{c['type']}</td><td>{c['version']}</td></tr>"

            return f"""<html>
<head><title>Nexus AI Configuration Bundle</title></head>
<body>
  <h1>Nexus AI Configuration Bundle</h1>
  <p><b>Exporter:</b> {bundle['exporter']}</p>
  <p><b>Version:</b> {bundle['version']}</p>
  <table border="1">
    <thead><tr><th>Capability ID</th><th>Name</th><th>Type</th><th>Version</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</body>
</html>"""

        else:
            raise ValueError(f"Unsupported export format: {format_name}")
