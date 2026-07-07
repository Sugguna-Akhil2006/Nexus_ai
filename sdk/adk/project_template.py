"""ProjectTemplate - generates new ADK project scaffolds (nexus new ...)."""

from __future__ import annotations

import os
from typing import Dict


class ProjectTemplate:
    """Generates new Nexus ADK project directory structures and starter files.

    Supports project types:
    - ``agent``: A standalone AI agent project.
    - ``workflow``: A workflow-only project.
    - ``plugin``: A plugin extension project.
    - ``provider``: A custom LLM provider project.
    """

    SUPPORTED_TYPES = ("agent", "workflow", "plugin", "provider")

    def generate(self, project_type: str, project_name: str, output_dir: str = ".") -> Dict[str, str]:
        """Generates project files and directories.

        Args:
            project_type: One of ``"agent"``, ``"workflow"``, ``"plugin"``, ``"provider"``.
            project_name: Identifier used for class and directory naming.
            output_dir: Target output directory path.

        Returns:
            Dictionary mapping relative file paths to generated file content.

        Raises:
            ValueError: If the project type is unsupported.
        """
        if project_type not in self.SUPPORTED_TYPES:
            raise ValueError(
                f"Unsupported project type '{project_type}'. "
                f"Choose from: {self.SUPPORTED_TYPES}"
            )

        generator = getattr(self, f"_generate_{project_type}")
        return generator(project_name, output_dir)

    def _generate_agent(self, name: str, output_dir: str) -> Dict[str, str]:
        class_name = "".join(w.capitalize() for w in name.split("_"))
        files = {
            f"{name}/agent.py": f'''"""ADK Agent: {name}."""

from sdk.adk.agent_builder import AgentBuilder
from sdk.adk.tool_builder import tool


@tool
def greet(context: dict) -> str:
    """Returns a greeting message."""
    return "Hello from {class_name}!"


agent_config = (
    AgentBuilder()
    .name("{class_name}")
    .description("A Nexus ADK agent.")
    .model("gpt-4")
    .provider("openai")
    .tool("greet", greet, "Returns a greeting")
    .memory("in_memory")
    .build()
)
''',
            f"{name}/README.md": f"# {class_name} Agent\n\nA Nexus ADK agent project.\n",
            f"{name}/__init__.py": "",
            f"{name}/tests/__init__.py": "",
            f"{name}/tests/test_{name}.py": f'''"""Tests for {name} agent."""

import unittest
from {name}.agent import agent_config


class Test{class_name}Agent(unittest.TestCase):
    def test_config_built(self):
        self.assertEqual(agent_config.name, "{class_name}")

if __name__ == "__main__":
    unittest.main()
''',
        }
        self._write_files(files, output_dir)
        return files

    def _generate_workflow(self, name: str, output_dir: str) -> Dict[str, str]:
        class_name = "".join(w.capitalize() for w in name.split("_"))
        files = {
            f"{name}/workflow.py": f'''"""ADK Workflow: {name}."""

from sdk.adk.workflow_builder import WorkflowBuilder


def step_one(context: dict) -> str:
    return "step_one_result"


workflow = (
    WorkflowBuilder()
    .sequential("step_one", step_one, timeout_seconds=15.0)
    .build()
)
''',
            f"{name}/README.md": f"# {class_name} Workflow\n\nA Nexus ADK workflow project.\n",
            f"{name}/__init__.py": "",
        }
        self._write_files(files, output_dir)
        return files

    def _generate_plugin(self, name: str, output_dir: str) -> Dict[str, str]:
        class_name = "".join(w.capitalize() for w in name.split("_"))
        files = {
            f"{name}/plugin.py": f'''"""ADK Plugin: {name}."""

from sdk.adk.plugin_builder import PluginBuilder

manifest = (
    PluginBuilder()
    .name("{name}")
    .version("1.0.0")
    .description("Custom Nexus plugin.")
    .capability("custom")
    .build()
)

# Auto-scaffold plugin class files
files = PluginBuilder().name("{name}").build()
''',
            f"{name}/README.md": f"# {class_name} Plugin\n\nA Nexus ADK plugin project.\n",
            f"{name}/__init__.py": "",
        }
        self._write_files(files, output_dir)
        return files

    def _generate_provider(self, name: str, output_dir: str) -> Dict[str, str]:
        class_name = "".join(w.capitalize() for w in name.split("_"))
        files = {
            f"{name}/provider.py": f'''"""ADK Provider: {name}."""

from sdk.adk.provider_builder import ProviderBuilder

provider_config = (
    ProviderBuilder()
    .provider("{name}")
    .model("custom-model-v1")
    .api_key_env("{name.upper()}_API_KEY")
    .temperature(0.7)
    .build()
)
''',
            f"{name}/README.md": f"# {class_name} Provider\n\nA Nexus ADK custom LLM provider project.\n",
            f"{name}/__init__.py": "",
        }
        self._write_files(files, output_dir)
        return files

    @staticmethod
    def _write_files(files: Dict[str, str], output_dir: str) -> None:
        """Writes generated files to the filesystem."""
        for rel_path, content in files.items():
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
