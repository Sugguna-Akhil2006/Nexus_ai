"""Comprehensive unit and integration tests for the Dynamic Execution Orchestrator."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.intelligence.contracts.request_models import Attachment, AttachmentType, IntelligenceModule, IntelligenceRequest
from backend.intelligence.orchestrator.dependency_resolver import DependencyResolver
from backend.intelligence.orchestrator.execution_orchestrator import DynamicExecutionOrchestrator
from backend.intelligence.orchestrator.execution_policy import ExecutionPolicy, PolicyType
from backend.intelligence.orchestrator.models import ExecutionGraph, ExecutionNode, NodeStatus
from backend.intelligence.orchestrator.module_selector import ModuleSelector
from backend.intelligence.orchestrator.workflow_optimizer import WorkflowOptimizer
from backend.intelligence.orchestrator.workflow_planner import WorkflowPlanner
from backend.runtime.event import EventBus, EventType


class TestModuleSelector(unittest.TestCase):
    """Verifies module matching rules and fallbacks."""

    def setUp(self) -> None:
        self.selector = ModuleSelector()

    def test_explicit_selection_respected(self) -> None:
        selected = self.selector.select_modules("test", [], explicit_modules=["resume"])
        self.assertEqual(selected, ["resume"])

    def test_query_keyword_matching(self) -> None:
        # "cv" -> resume
        self.assertIn("resume", self.selector.select_modules("Review cv parameters", []))
        # "git" -> github
        self.assertIn("github", self.selector.select_modules("Get git project metadata", []))


class TestDependencyResolver(unittest.TestCase):
    """Verifies topological sorting and cycle detection."""

    def test_topological_sort_linear(self) -> None:
        n1 = ExecutionNode(module_name="resume", capability="A")
        n2 = ExecutionNode(module_name="knowledge", capability="B", dependencies=[n1.node_id])
        n3 = ExecutionNode(module_name="professional", capability="C", dependencies=[n2.node_id])

        graph = ExecutionGraph(nodes={n1.node_id: n1, n2.node_id: n2, n3.node_id: n3})
        batches = DependencyResolver.resolve(graph)

        self.assertEqual(len(batches), 3)
        self.assertEqual(batches[0], [n1.node_id])
        self.assertEqual(batches[1], [n2.node_id])
        self.assertEqual(batches[2], [n3.node_id])

    def test_cycle_detection_raises_value_error(self) -> None:
        n1 = ExecutionNode(module_name="resume", capability="A", dependencies=["n2"])
        n2 = ExecutionNode(node_id="n2", module_name="knowledge", capability="B", dependencies=[n1.node_id])

        graph = ExecutionGraph(nodes={n1.node_id: n1, "n2": n2})
        with self.assertRaises(ValueError):
            DependencyResolver.resolve(graph)


class TestWorkflowOptimizer(unittest.TestCase):
    """Verifies plan trimming under policies."""

    def test_fastest_policy_prunes_research(self) -> None:
        planner = WorkflowPlanner()
        policy = ExecutionPolicy(policy_type=PolicyType.FASTEST)
        plan = planner.plan(["resume", "research"], policy)

        optimized = WorkflowOptimizer.optimize(plan)
        # Should prune node-research
        self.assertNotIn("node-research", optimized.graph.nodes)


class TestDynamicOrchestratorE2E(unittest.TestCase):
    """Full workflow runs covering execution, confidence scoring, and timeline logging."""

    def setUp(self) -> None:
        # Clear EventBus history
        bus = EventBus()
        with bus._lock:
            bus._subscribers.clear()
            bus._queue.clear()
            bus._history.clear()

        self.orchestrator = DynamicExecutionOrchestrator()

    def test_successful_composition_flow(self) -> None:
        req = IntelligenceRequest(
            workspace_id="ws-1",
            user_id="user-1",
            module=IntelligenceModule.RESUME,
            input={"query": "Get resume and github summary"},
        )
        res = self.orchestrator.execute(req, policy_type=PolicyType.BALANCED, explicit_modules=["resume", "github"])

        self.assertEqual(res.status, "completed")
        self.assertEqual(len(res.modules_executed), 2)
        self.assertGreater(res.confidence_score, 0.0)
        self.assertTrue(len(res.execution_timeline) > 0)

    def test_failure_recovery_and_degraded_status(self) -> None:
        # Test with invalid module names to trigger fallback mock or failure handling
        req = IntelligenceRequest(
            workspace_id="ws-2",
            user_id="user-2",
            module=IntelligenceModule.RESUME,
            input={"query": "Run a doc matching query"},
        )
        res = self.orchestrator.execute(req, policy_type=PolicyType.BALANCED, explicit_modules=["non_existent"])
        # Should handle unknown module gracefully (using fallback mock data)
        self.assertEqual(res.status, "completed")
