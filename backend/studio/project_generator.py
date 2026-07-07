"""Project Generator scaffolding standardized boilerplate templates for extension components."""

from __future__ import annotations

import os
from typing import Optional


class ProjectGenerator:
    """Generates standardized project templates to accelerate custom implementations."""

    def generate_component(self, component_type: str, name: str, output_dir: str) -> str:
        """Scaffolds a component template folder and files.

        Args:
            component_type: module, tool, workflow, provider, plugin.
            name: Component name (e.g. "SlackConnector").
            output_dir: Target output directory.

        Returns:
            str: Path to the generated folder.
        """
        t = component_type.lower()
        target_path = os.path.abspath(os.path.join(output_dir, name))
        os.makedirs(target_path, exist_ok=True)

        if t == "module":
            self._write_file(target_path, "module.py", f"""class Custom{name}Module:
    def __init__(self):
        self.name = "{name}"
""")
        elif t == "tool":
            self._write_file(target_path, "tool.py", f"""class Custom{name}Tool:
    def execute(self, params: dict) -> dict:
        return {{"status": "success", "tool": "{name}"}}
""")
        elif t == "workflow":
            self._write_file(target_path, "workflow.json", f"""{{
  "workflow_id": "wf-{name.lower()}",
  "name": "{name}",
  "steps": []
}}""")
        elif t == "provider":
            self._write_file(target_path, "provider.py", f"""class Custom{name}Provider:
    def initialize(self) -> None:
        pass
""")
        elif t == "plugin":
            self._write_file(target_path, "plugin.py", f"""class Custom{name}Plugin:
    def install(self) -> None:
        pass
""")
        else:
            raise ValueError(f"Unsupported component type for generation: {component_type}")

        return target_path

    def _write_file(self, folder: str, filename: str, content: str) -> None:
        with open(os.path.join(folder, filename), "w") as f:
            f.write(content)
