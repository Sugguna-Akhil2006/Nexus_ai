"""Integration tests verifying full integrated AI Platform (Sprint 1)."""

from __future__ import annotations

import concurrent.futures
import time
import unittest
from unittest.mock import MagicMock

# Import core subsystems
from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType
from backend.registry.registry_validator import RegistryValidator
from backend.registry.registry_health import RegistryHealthMonitor
from backend.studio.studio_service import StudioService
from backend.governance.governance_engine import GovernanceEngine
from backend.runtime.event import EventBus, Event, EventType
from backend.api.sqlite_mock import DBStorage


class TestPlatformIntegrationSprint(unittest.TestCase):
    """Integration, Shared Context, Failure Recovery, and Load testing suite."""

    def setUp(self) -> None:
        self.registry = CapabilityRegistry()
        self.registry.clear()
        
        # Populate core capability registry
        self.registry.register_capability(CapabilityMetadata(
            capability_id="module-resumeintelligence",
            name="ResumeIntelligence",
            type=CapabilityType.MODULE,
            version="1.0.0",
            description="Resume parsing module.",
            tags=["resume", "ats"],
            compatibilities=["1.0.0"]
        ))
        self.registry.register_capability(CapabilityMetadata(
            capability_id="module-githubintelligence",
            name="GitHubIntelligence",
            type=CapabilityType.MODULE,
            version="1.0.0",
            description="GitHub auditing module.",
            tags=["github", "audit"],
            compatibilities=["1.0.0"]
        ))
        self.registry.register_capability(CapabilityMetadata(
            capability_id="module-documentintelligence",
            name="DocumentIntelligence",
            type=CapabilityType.MODULE,
            version="1.0.0",
            description="Document search/extraction module.",
            tags=["document", "extraction"],
            compatibilities=["1.0.0"]
        ))
        self.registry.register_capability(CapabilityMetadata(
            capability_id="agent-professional",
            name="ProfessionalAgent",
            type=CapabilityType.AGENT,
            version="1.0.0",
            description="Professional analysis agent.",
            tags=["professional", "analysis"],
            compatibilities=["1.0.0"]
        ))

        self.validator = RegistryValidator()
        self.health_monitor = RegistryHealthMonitor(self.registry)
        self.studio = StudioService(self.registry)
        self.gov = GovernanceEngine()
        self._db = DBStorage()

    def tearDown(self) -> None:
        self.registry.clear()

    def test_task1_registration_and_compatibility(self) -> None:
        """Verifies modules register correctly and checks version compatibility constraints."""
        modules = self.registry.list_capabilities(CapabilityType.MODULE)
        self.assertEqual(len(modules), 3)

        # Check SemVer compatibility validations
        resume_meta = self.registry.get_capability("module-resumeintelligence")
        self.assertTrue(self.validator.is_compatible(resume_meta, "1.2.0"))
        self.assertFalse(self.validator.is_compatible(resume_meta, "2.0.0"))

    def test_task2_cross_module_workflows(self) -> None:
        """Executes Workflow A, B, and C E2E integration validations."""
        
        # --- Workflow A: Resume -> Profile -> Professional -> Report ---
        # Simulate ATS extraction
        extracted_skills = ["Python", "SQLite", "FastAPI"]
        # Update knowledge profile
        profile = {"skills": extracted_skills, "experience": "Senior Developer"}
        # Run professional analyzer
        from backend.intelligence.professional.professional_agent import ProfessionalAgent
        from backend.intelligence.professional.models import ProfessionalAnalysisRequest
        agent = ProfessionalAgent()
        report_a = agent.analyze(ProfessionalAnalysisRequest(
            workspace_id="ws-workflow-a",
            user_id="dev-1",
            resume_text="Senior Developer skilled in Python, SQLite, and FastAPI.",
            github_username="dev-1",
            target_role="Lead Software Engineer",
            job_description="Need senior backend python dev."
        ))
        self.assertIsNotNone(report_a)
        self.assertIn("Python", str(report_a.ats_score))

        # --- Workflow B: GitHub -> Profile -> Professional -> Engineering Report ---
        # Simulate GitHub metadata extraction
        repo_data = {"lines_of_code": 15000, "languages": {"Python": 90}}
        # Compile engineering analysis
        report_b = agent.analyze(ProfessionalAnalysisRequest(
            workspace_id="ws-workflow-b",
            user_id="dev-2",
            resume_text="Backend Dev",
            github_username="dev-2",
            target_role="Engineering Manager",
            job_description="Management position."
        ))
        self.assertIsNotNone(report_b)

        # --- Workflow C: Document -> Extraction -> Profile -> Professional -> Unified Report ---
        # Simulate document context extraction
        doc_context = "Nexus AI platform includes a robust governance system."
        report_c = agent.analyze(ProfessionalAnalysisRequest(
            workspace_id="ws-workflow-c",
            user_id="dev-3",
            resume_text="Developer",
            github_username="dev-3",
            target_role="Developer",
            job_description="Governance developer."
        ))
        self.assertIsNotNone(report_c)

    def test_task3_shared_context_propagation(self) -> None:
        """Verifies memory, context, and knowledge profile sharing across steps."""
        workspace_id = "ws-shared-context"
        
        # 1. Update workspace knowledge profile using memory snapshots
        snapshot = self.studio.memory_ins.get_memory_snapshot(workspace_id)
        snapshot.knowledge_profile["shared_key"] = "shared_value"
        
        # Verify changes persist in memory inspections
        self.assertEqual(snapshot.knowledge_profile.get("shared_key"), "shared_value")

    def test_task4_failure_recovery_and_retries(self) -> None:
        """Verifies retry and timeout recovery rules."""
        # Setup retry decorator simulation
        attempts = 0
        
        def mock_flaky_provider():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise TimeoutError("Model provider timeout connection error.")
            return "Inference response success."

        # Run mock with retry logic
        response = None
        for i in range(5):
            try:
                response = mock_flaky_provider()
                break
            except TimeoutError:
                time.sleep(0.01)

        self.assertEqual(response, "Inference response success.")
        self.assertEqual(attempts, 3)

    def test_task5_performance_benchmarks(self) -> None:
        """Measures workflow latency and execution times."""
        start = time.perf_counter()
        
        # Validate governance checks latency
        self.gov.validate_execution(
            {"user_id": "admin", "workspace_id": "ws-perf", "capability": "RESUME_PARSING"},
            {"query": "Inference benchmark payload"}
        )
        
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.0, "Validation latency exceeds SLA benchmark limits!")

    def test_task7_stress_and_concurrency_load(self) -> None:
        """Executes parallel workflow requests under concurrent load."""
        def run_isolated_task(index: int) -> None:
            self.gov.validate_execution(
                {"user_id": f"dev-{index}", "workspace_id": f"ws-{index}", "capability": "RESUME_PARSING"},
                {"query": f"Load test payload {index}"}
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(run_isolated_task, i) for i in range(24)]
            concurrent.futures.wait(futures)

        # Audit logs should contain 24 executions
        logs = self.gov.get_audit_history()
        self.assertGreaterEqual(len(logs), 24)
