"""Integration tests for Core Intelligence Orchestrator Framework."""

import time
import unittest
from typing import Set

from backend.intelligence.core.base_intelligence import BaseIntelligenceModule
from backend.intelligence.core.context import IntelligenceContext
from backend.intelligence.core.state import ExecutionState
from backend.intelligence.core.workflow import PipelineStage
from backend.intelligence.core.pipeline import IntelligencePipeline
from backend.intelligence.core.orchestrator import IntelligenceOrchestrator
from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.core.report import IntelligenceExecutionReport
from backend.intelligence.core.exceptions import RegistryError


class DummyModule(BaseIntelligenceModule):
    """Mock module for testing framework registration and execution."""

    def __init__(self, name: str, capabilities: Set[str]) -> None:
        self._name = name
        self._capabilities = capabilities

    @property
    def name(self) -> str:
        return self._name

    @property
    def capabilities(self) -> Set[str]:
        return self._capabilities

    def execute_workflow(self, context: IntelligenceContext) -> IntelligenceExecutionReport:
        pipeline = IntelligencePipeline()
        
        # Define sample pipeline stages
        def step1(ctx, state):
            ctx.intermediate_results["step1"] = "done"

        pipeline.add_stage(PipelineStage(name="Step1", action=step1))
        
        orchestrator = IntelligenceOrchestrator(self.name, pipeline)
        return orchestrator.run(context)


class TestCoreOrchestrator(unittest.TestCase):
    """Verifies registry lookup, concurrency pools, retry loops, and telemetry output."""

    def setUp(self) -> None:
        self.registry = IntelligenceRegistry()

    def test_module_registration(self) -> None:
        """Verifies registering a module and finding it by capability."""
        module = DummyModule("TestModule", {"TEST_CAP"})
        self.registry.register(module)

        # Retrieve by name
        retrieved = self.registry.get_module("TestModule")
        self.assertEqual(retrieved.name, "TestModule")

        # Retrieve by capability
        matches = self.registry.get_modules_by_capability("TEST_CAP")
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].name, "TestModule")

        # Assert unregistered throws RegistryError
        with self.assertRaises(RegistryError):
            self.registry.get_module("Unregistered")

    def test_pipeline_execution_success(self) -> None:
        """Verifies simple sequential stage execution."""
        module = DummyModule("SequentialModule", {"SEQ_CAP"})
        context = IntelligenceContext(workspace_id="ws-seq")
        
        report = module.execute_workflow(context)
        self.assertEqual(report.status, "completed")
        self.assertEqual(report.stage_results["step1"], "done")

    def test_parallel_execution(self) -> None:
        """Verifies that independent stages are executed concurrently in a ThreadPoolExecutor."""
        pipeline = IntelligencePipeline()
        
        # Group independent stages that sleep for 0.4 seconds each
        def slow_stage_1(ctx, state):
            time.sleep(0.4)
            ctx.intermediate_results["s1"] = "ok"

        def slow_stage_2(ctx, state):
            time.sleep(0.4)
            ctx.intermediate_results["s2"] = "ok"

        pipeline.add_stage(PipelineStage(name="Slow1", action=slow_stage_1))
        pipeline.add_stage(PipelineStage(name="Slow2", action=slow_stage_2))

        context = IntelligenceContext(workspace_id="ws-parallel")
        state = ExecutionState()

        start = time.perf_counter()
        pipeline.execute(context, state)
        duration = time.perf_counter() - start

        # If sequential, total time >= 0.8s. If parallel, it should be ~0.4s.
        self.assertLess(duration, 0.7)
        self.assertEqual(context.intermediate_results["s1"], "ok")
        self.assertEqual(context.intermediate_results["s2"], "ok")

    def test_retry_recovery(self) -> None:
        """Verifies that transient failures in a stage are retried and can recover."""
        pipeline = IntelligencePipeline()
        call_count = 0

        def transient_action(ctx, state):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Transient database lock")
            ctx.intermediate_results["recovered"] = "yes"

        pipeline.add_stage(PipelineStage(name="RetryStage", action=transient_action, max_retries=3))

        context = IntelligenceContext(workspace_id="ws-retry")
        state = ExecutionState()
        pipeline.execute(context, state)

        self.assertEqual(call_count, 2)
        self.assertEqual(state.retry_counts["RetryStage"], 1)
        self.assertEqual(context.intermediate_results["recovered"], "yes")

    def test_failure_recovery_partial(self) -> None:
        """Verifies that non-dependent stage failures do not abort the entire pipeline."""
        pipeline = IntelligencePipeline()

        def fail_action(ctx, state):
            raise Exception("Failure in non-critical stage")

        def succeed_action(ctx, state):
            ctx.intermediate_results["succeed"] = "yes"

        pipeline.add_stage(PipelineStage(name="FailStage", action=fail_action, max_retries=1))
        pipeline.add_stage(PipelineStage(name="SucceedStage", action=succeed_action))

        context = IntelligenceContext(workspace_id="ws-partial")
        orchestrator = IntelligenceOrchestrator("PartialModule", pipeline)
        report = orchestrator.run(context)

        self.assertEqual(report.status, "partial_success")
        self.assertIn("FailStage", report.errors)
        self.assertEqual(report.stage_results["succeed"], "yes")
