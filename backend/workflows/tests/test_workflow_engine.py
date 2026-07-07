"""Comprehensive tests for the AI Workflow Automation Engine."""

import threading
import time
import unittest
from typing import Any, Dict

from backend.workflows.models import (
    ExecutionStatus,
    ParallelBranch,
    StepType,
    WorkflowStep,
)
from backend.workflows.workflow_builder import WorkflowBuilder
from backend.workflows.workflow_engine import WorkflowEngine
from backend.workflows.workflow_executor import WorkflowExecutor, StepHandler
from backend.workflows.workflow_context import WorkflowContext
from backend.workflows.workflow_validator import WorkflowValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine(**kwargs) -> WorkflowEngine:
    """Creates a WorkflowEngine with optional custom step handlers."""
    return WorkflowEngine(**kwargs)


def _noop_handler(step, ctx) -> Dict[str, Any]:
    return {"result": f"done:{step.name}"}


def _failing_handler(step, ctx) -> Dict[str, Any]:
    raise RuntimeError("Simulated step failure")


def _slow_handler(step, ctx) -> Dict[str, Any]:
    time.sleep(10)  # intentionally exceeds any short timeout
    return {}


def _flaky_call_count(counter: dict):
    """Returns a handler that fails on the first call, succeeds on the second."""
    def handler(step, ctx):
        counter["calls"] = counter.get("calls", 0) + 1
        if counter["calls"] == 1:
            raise RuntimeError("Transient failure")
        return {"result": "recovered"}
    return handler


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestSimpleWorkflow(unittest.TestCase):
    """Verifies sequential step execution and COMPLETED status."""

    def test_sequential_steps_complete(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("Simple Workflow")
            .add_step("Step A", StepType.RESUME)
            .add_step("Step B", StepType.GITHUB)
            .add_step("Step C", StepType.DOCUMENT)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id, workspace_id="ws-1")

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(len(result.step_results), 3)
        self.assertTrue(all(sr.status == ExecutionStatus.COMPLETED for sr in result.step_results))

    def test_history_persisted(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("History Test")
            .add_step("Only Step", StepType.REASONING)
            .build()
        )
        engine.create_workflow(definition)
        exec_result = engine.execute_workflow(definition.workflow_id)

        history = engine.get_history(definition.workflow_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].execution_id, exec_result.execution_id)


class TestParallelWorkflow(unittest.TestCase):
    """Verifies parallel branch execution."""

    def test_parallel_branches_complete(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        branch_a = ParallelBranch(
            name="Branch A",
            steps=[WorkflowStep(name="Doc Analysis", step_type=StepType.DOCUMENT)],
        )
        branch_b = ParallelBranch(
            name="Branch B",
            steps=[WorkflowStep(name="Research Synthesis", step_type=StepType.RESEARCH)],
        )
        definition = (
            WorkflowBuilder("Parallel Workflow")
            .add_parallel_branch("Branch A", branch_a.steps)
            .add_parallel_branch("Branch B", branch_b.steps)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        # Both branch steps should appear in step_results
        names = {sr.step_name for sr in result.step_results}
        self.assertIn("Doc Analysis", names)
        self.assertIn("Research Synthesis", names)


class TestConditionalWorkflow(unittest.TestCase):
    """Verifies conditional step skipping."""

    def test_step_skipped_when_condition_false(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("Conditional Workflow")
            .add_step("Always Run", StepType.RESUME)
            .add_step(
                "Conditional Step",
                StepType.REASONING,
                condition="score > 100",  # will never be True with default vars
            )
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        statuses = {sr.step_name: sr.status for sr in result.step_results}
        self.assertEqual(statuses["Always Run"], ExecutionStatus.COMPLETED)
        self.assertEqual(statuses["Conditional Step"], ExecutionStatus.SKIPPED)

    def test_step_runs_when_condition_true(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("Conditional True Workflow")
            .add_step("Always Run", StepType.RESUME)
            .add_step(
                "Conditional Step",
                StepType.REASONING,
                condition="ready == True",
            )
            .set_variable("ready", True)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        statuses = {sr.step_name: sr.status for sr in result.step_results}
        self.assertEqual(statuses["Conditional Step"], ExecutionStatus.COMPLETED)


class TestRetryLogic(unittest.TestCase):
    """Verifies retry behaviour on transient failures."""

    def test_step_recovers_on_retry(self):
        counter: dict = {}
        engine = _make_engine(
            step_handlers={t: _flaky_call_count(counter) for t in StepType}
        )
        definition = (
            WorkflowBuilder("Retry Workflow")
            .add_step("Flaky Step", StepType.RESUME, max_retries=1)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(result.step_results[0].attempts, 2)

    def test_step_fails_after_all_retries_exhausted(self):
        engine = _make_engine(
            step_handlers={t: _failing_handler for t in StepType}
        )
        definition = (
            WorkflowBuilder("Exhausted Retries Workflow")
            .add_step("Always Fail", StepType.RESUME, max_retries=2)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertEqual(result.step_results[0].attempts, 3)  # 1 original + 2 retries


class TestTimeout(unittest.TestCase):
    """Verifies timeout enforcement on slow steps."""

    def test_step_times_out(self):
        engine = _make_engine(
            step_handlers={t: _slow_handler for t in StepType}
        )
        definition = (
            WorkflowBuilder("Timeout Workflow")
            .add_step("Slow Step", StepType.RESUME, timeout_seconds=0.2)
            .build()
        )
        engine.create_workflow(definition)
        result = engine.execute_workflow(definition.workflow_id)

        self.assertEqual(result.status, ExecutionStatus.TIMED_OUT)
        self.assertEqual(result.step_results[0].status, ExecutionStatus.TIMED_OUT)


class TestLargeWorkflow(unittest.TestCase):
    """Verifies performance budget for workflows with many steps."""

    def test_large_workflow_completes_fast(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        builder = WorkflowBuilder("Large Workflow")
        for i in range(15):
            builder.add_step(f"Step {i}", StepType.NO_OP)
        definition = builder.build()
        engine.create_workflow(definition)

        start = time.perf_counter()
        result = engine.execute_workflow(definition.workflow_id)
        duration = time.perf_counter() - start

        self.assertEqual(result.status, ExecutionStatus.COMPLETED)
        self.assertEqual(len(result.step_results), 15)
        self.assertLess(duration, 2.0, "Large workflow exceeded 2-second budget.")


class TestConcurrentExecution(unittest.TestCase):
    """Verifies thread-safe concurrent workflow executions."""

    def test_concurrent_executions_are_isolated(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("Concurrent Workflow")
            .add_step("Step X", StepType.RESUME)
            .build()
        )
        engine.create_workflow(definition)

        results = []
        errors = []

        def run():
            try:
                r = engine.execute_workflow(definition.workflow_id, workspace_id="ws-concurrent")
                results.append(r)
            except Exception as e:
                errors.append(str(e))

        threads = [threading.Thread(target=run) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors in concurrent execution: {errors}")
        self.assertEqual(len(results), 8)
        self.assertTrue(all(r.status == ExecutionStatus.COMPLETED for r in results))

    def test_metrics_accurate_after_concurrent_runs(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        definition = (
            WorkflowBuilder("Metrics Workflow")
            .add_step("Metric Step", StepType.NO_OP)
            .build()
        )
        engine.create_workflow(definition)

        threads = [
            threading.Thread(target=engine.execute_workflow, args=(definition.workflow_id,))
            for _ in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = engine.get_metrics_summary()
        self.assertEqual(summary["total_executions"], 5)
        self.assertEqual(summary["succeeded"], 5)


class TestWorkflowTemplates(unittest.TestCase):
    """Verifies pre-built templates are discoverable and executable."""

    def test_templates_are_listed(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        templates = engine.list_templates()
        self.assertIn("resume_analysis_workflow", templates)
        self.assertIn("github_engineering_workflow", templates)
        self.assertIn("document_research_workflow", templates)

    def test_resume_template_executes(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        result = engine.execute_template("resume_analysis_workflow")
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)

    def test_github_template_executes(self):
        engine = _make_engine(step_handlers={t: _noop_handler for t in StepType})
        result = engine.execute_template("github_engineering_workflow")
        self.assertEqual(result.status, ExecutionStatus.COMPLETED)


class TestWorkflowValidator(unittest.TestCase):
    """Verifies structural validation rejects invalid definitions."""

    def test_empty_name_rejected(self):
        with self.assertRaises(WorkflowValidationError):
            engine = _make_engine()
            definition = (
                WorkflowBuilder("")
                .add_step("Step", StepType.NO_OP)
                .build()
            )
            engine.create_workflow(definition)

    def test_no_steps_rejected(self):
        from backend.workflows.workflow_validator import WorkflowValidator
        from backend.workflows.models import WorkflowDefinition
        validator = WorkflowValidator()
        with self.assertRaises(WorkflowValidationError):
            validator.validate(WorkflowDefinition(name="Empty Workflow"))

    def test_duplicate_step_id_rejected(self):
        from backend.workflows.workflow_validator import WorkflowValidator
        from backend.workflows.models import WorkflowDefinition
        validator = WorkflowValidator()
        step_a = WorkflowStep(step_id="dup-id", name="Step A", step_type=StepType.NO_OP)
        step_b = WorkflowStep(step_id="dup-id", name="Step B", step_type=StepType.NO_OP)
        with self.assertRaises(WorkflowValidationError):
            validator.validate(WorkflowDefinition(name="Dup Workflow", steps=[step_a, step_b]))


if __name__ == "__main__":
    unittest.main()
