"""Unit tests for Nexus Studio Developer Experience Platform."""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType
from backend.studio.models import *
from backend.studio.studio_service import StudioService


class TestNexusStudio(unittest.TestCase):
    """Test suite covering Studio inspectors, metrics, and template generators."""

    def setUp(self) -> None:
        self.registry = CapabilityRegistry()
        self.registry.clear()
        
        # Pre-populate custom mock capabilities for studio test runs
        self.registry.register_capability(CapabilityMetadata(
            capability_id="agent-professional",
            name="ProfessionalAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Agent capability.",
            tags=["nlp"],
            extra={
                "execution_logs": [
                    {"execution_id": "exec-999", "status": "completed", "latency_ms": 150.0}
                ]
            }
        ))

        self.registry.register_capability(CapabilityMetadata(
            capability_id="provider-llm-ollama",
            name="Ollama",
            type=CapabilityType.LLM_PROVIDER,
            version="1.0.0",
            description="Ollama local LLM",
            extra={"cost_rate": 0.0}
        ))

        self.studio = StudioService(self.registry)
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        self.registry.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_studio_health_and_workspace_overview(self) -> None:
        """Verifies health dashboard indicators and workspace metrics overview aggregation."""
        health = self.studio.get_studio_health_status()
        self.assertEqual(health["runtime_health"], "healthy")
        self.assertEqual(health["agent_health"], "healthy")

        overview = self.studio.get_workspace_overview("ws-123")
        self.assertEqual(overview["workspace_id"], "ws-123")
        self.assertGreaterEqual(overview["memory_usage_bytes"], 0)

    def test_agent_and_workflow_inspectors(self) -> None:
        """Verifies agent capabilities inspection and execution history resolution."""
        agent_info = self.studio.agent_ins.inspect_agent("ProfessionalAgent")
        self.assertIsNotNone(agent_info)
        self.assertEqual(agent_info.name, "ProfessionalAgent")
        self.assertEqual(len(agent_info.execution_history), 1)
        self.assertEqual(agent_info.execution_history[0]["execution_id"], "exec-999")

        # Verify execution visualizer timeline offsets compilation
        timeline = self.studio.visualizer.compile_execution_timeline(agent_info.execution_history)
        self.assertEqual(len(timeline), 1)
        self.assertEqual(timeline[0]["start_offset_ms"], 0.0)
        self.assertEqual(timeline[0]["duration_ms"], 150.0)

    def test_provider_dashboard_metrics(self) -> None:
        """Verifies provider dashboards compile cost metrics correctly."""
        metrics = self.studio.provider_dash.get_provider_metrics()
        self.assertGreater(len(metrics), 0)
        self.assertTrue(any(m.name == "Ollama" for m in metrics))
        ollama_metric = next(m for m in metrics if m.name == "Ollama")
        self.assertEqual(ollama_metric.cost_per_1k_tokens, 0.0)

    def test_configuration_bundles_and_exports(self) -> None:
        """Verifies markdown and HTML exports are formatted successfully."""
        markdown_str = self.studio.config_mgr.export_as("markdown")
        self.assertIn("# Nexus AI Configuration Bundle", markdown_str)
        self.assertIn("agent-professional", markdown_str)

        html_str = self.studio.config_mgr.export_as("html")
        self.assertIn("<h1>Nexus AI Configuration Bundle</h1>", html_str)
        self.assertIn("agent-professional", html_str)

    def test_project_generators_boilerplate(self) -> None:
        """Verifies standardized file layout creation."""
        # 1. Scaffold module template
        module_path = self.studio.generator.generate_component("module", "TestEngine", self.temp_dir)
        self.assertTrue(os.path.exists(module_path))
        self.assertTrue(os.path.exists(os.path.join(module_path, "module.py")))

        # 2. Scaffold tool template
        tool_path = self.studio.generator.generate_component("tool", "SlackSearch", self.temp_dir)
        self.assertTrue(os.path.exists(tool_path))
        self.assertTrue(os.path.exists(os.path.join(tool_path, "tool.py")))
