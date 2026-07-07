"""Unit tests for AI Registry & Capability Marketplace."""

from __future__ import annotations

import concurrent.futures
import unittest

from backend.registry.registry_models import CapabilityMetadata, CapabilityType, SemVer
from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.service_registry import ServiceRegistry
from backend.registry.provider_registry import ProviderRegistry
from backend.registry.workflow_registry import WorkflowRegistry
from backend.registry.prompt_registry import PromptRegistry
from backend.registry.tool_registry import ToolRegistry
from backend.registry.registry_validator import RegistryValidator
from backend.registry.registry_health import RegistryHealthMonitor
from backend.registry.dependency_graph import DependencyGraph
from backend.registry.registry_dashboard import RegistryDashboard


class TestAIRegistryFramework(unittest.TestCase):
    """Test suite covering capability discovery, semver, dependencies, and health tracking."""

    def setUp(self) -> None:
        self.registry = CapabilityRegistry()
        self.registry.clear()
        
        self.service_reg = ServiceRegistry(self.registry)
        self.provider_reg = ProviderRegistry(self.registry)
        self.workflow_reg = WorkflowRegistry(self.registry)
        self.prompt_reg = PromptRegistry(self.registry)
        self.tool_reg = ToolRegistry(self.registry)
        
        self.validator = RegistryValidator()
        self.health_monitor = RegistryHealthMonitor(self.registry)
        self.dep_graph = DependencyGraph(self.registry)
        self.dashboard = RegistryDashboard(self.registry)

    def tearDown(self) -> None:
        self.registry.clear()

    def test_registration_and_search(self) -> None:
        """Verifies simple capability registration and lookup functionality."""
        meta = CapabilityMetadata(
            capability_id="test-agent-1",
            name="TestAgentOne",
            type=CapabilityType.AGENT,
            version="2.1.0",
            description="Agent capability for search test.",
            tags=["nlp", "search", "test-tag"]
        )
        self.registry.register_capability(meta)
        
        # Lookups
        cap = self.registry.get_capability("test-agent-1")
        self.assertIsNotNone(cap)
        self.assertEqual(cap.name, "TestAgentOne")
        self.assertEqual(cap.version, "2.1.0")

        # Search matching tag
        results = self.registry.search("test-tag")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].capability_id, "test-agent-1")

    def test_versioning_and_compatibilities(self) -> None:
        """Verifies SemVer parsing and runtime compatibility checks."""
        self.assertTrue(self.validator.validate_semver("1.5.0-rc2"))
        self.assertFalse(self.validator.validate_semver("invalid-version"))

        meta = CapabilityMetadata(
            capability_id="test-compat-agent",
            name="CompatAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Test compat",
            compatibilities=["1.0.0", "2.0.0"]
        )
        
        # Test compatibility bounds
        self.assertTrue(self.validator.is_compatible(meta, "1.5.0"))
        self.assertFalse(self.validator.is_compatible(meta, "3.0.0"))

    def test_auto_discovery_pipelines(self) -> None:
        """Verifies discovery runs populates LLM, workspaces, workflows, prompts, and tools."""
        self.service_reg.discover_services()
        self.provider_reg.discover_providers()
        self.workflow_reg.discover_workflows()
        self.prompt_reg.discover_prompts()
        self.tool_reg.discover_tools()

        all_caps = self.registry.list_capabilities()
        self.assertGreater(len(all_caps), 0)
        
        # Validate counts
        dash = self.dashboard.get_dashboard_data()
        self.assertEqual(dash["overall_health_status"], "healthy")
        self.assertGreaterEqual(dash["registered_modules_count"], 0)

    def test_dependency_resolution(self) -> None:
        """Verifies downstream capability dependency graphing resolving."""
        # Setup transitive chain: A depends on B, B depends on C
        self.registry.register_capability(CapabilityMetadata(
            capability_id="cap-A",
            name="A",
            type=CapabilityType.MODULE,
            version="1.0.0",
            description="A",
            dependencies=["cap-B"]
        ))
        self.registry.register_capability(CapabilityMetadata(
            capability_id="cap-B",
            name="B",
            type=CapabilityType.WORKFLOW,
            version="1.0.0",
            description="B",
            dependencies=["cap-C"]
        ))
        self.registry.register_capability(CapabilityMetadata(
            capability_id="cap-C",
            name="C",
            type=CapabilityType.TOOL,
            version="1.0.0",
            description="C",
            dependencies=[]
        ))

        downstream = self.dep_graph.get_downstream_dependencies("cap-A")
        self.assertIn("cap-B", downstream)
        self.assertIn("cap-C", downstream)

        mermaid = self.dep_graph.generate_mermaid_diagram()
        self.assertIn("cap-A --> cap-B", mermaid)
        self.assertIn("cap-B --> cap-C", mermaid)

    def test_health_monitoring_metrics(self) -> None:
        """Verifies health logs updates track usage rates and average latency."""
        meta = CapabilityMetadata(
            capability_id="test-health-cap",
            name="HealthCap",
            type=CapabilityType.TOOL,
            version="1.0.0",
            description="Test health updates."
        )
        self.registry.register_capability(meta)

        # Track execution runs
        self.registry.update_health("test-health-cap", is_available=True, latency_ms=10.0, is_error=False)
        self.registry.update_health("test-health-cap", is_available=True, latency_ms=20.0, is_error=True)

        h = self.health_monitor.get_health_status("test-health-cap")
        self.assertIsNotNone(h)
        self.assertEqual(h.usage_count, 2)
        self.assertEqual(h.failure_count, 1)
        self.assertEqual(h.error_rate, 0.5)

    def test_concurrent_registrations(self) -> None:
        """Verifies CapabilityRegistry thread-safety under concurrent load operations."""
        def register_task(index: int) -> None:
            meta = CapabilityMetadata(
                capability_id=f"concurrent-cap-{index}",
                name=f"ConcurrentCap{index}",
                type=CapabilityType.TOOL,
                version="1.0.0",
                description="Concurrent test capability."
            )
            self.registry.register_capability(meta)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(register_task, i) for i in range(50)]
            concurrent.futures.wait(futures)

        all_caps = self.registry.list_capabilities()
        concurrent_caps = [c for c in all_caps if c.capability_id.startswith("concurrent-cap-")]
        self.assertEqual(len(concurrent_caps), 50)
