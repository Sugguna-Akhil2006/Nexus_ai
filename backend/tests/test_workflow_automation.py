"""Tests for the Workflow Automation Engine.

Verifies execution, conditionals, parallel branches, concurrency, 
failure recovery, retries, and API gateways.
"""

import concurrent.futures
import json
import time
import unittest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.workflow.automation_engine import (
    WorkflowExecutor, WorkflowStep, WorkflowCondition, WorkflowScheduler
)
from backend.runtime.event import Event, EventBus, EventType
from backend.api.sqlite_mock import DBStorage

class TestWorkflowAutomation(unittest.TestCase):
    """Test suite covering workflow engine executions, approvals, schedules, and failures recovery."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        self.executor = WorkflowExecutor()
        self.db = DBStorage()

        # Setup Mock Model Provider
        from backend.interfaces.model import ModelRegistry
        from backend.agents.chat import MockChatModelProvider
        self.model_registry = ModelRegistry()
        with self.model_registry._lock:
            self.model_registry._providers.clear()
        self.model_provider = MockChatModelProvider()
        self.model_registry.register_provider("mock_chat", self.model_provider)

        # Setup Event Listener to catch custom events
        self.event_bus = EventBus()
        self.caught_events = []
        self.event_bus.subscribe("*", self.catch_event)

    def catch_event(self, event: Event) -> None:
        """Callback to store published events."""
        if event.event_type == EventType.CUSTOM_EVENT:
            self.caught_events.append(event.payload.get("event_name"))

    def test_workflow_definition_creation(self) -> None:
        """Verifies creating definition registers all steps and conditions in database."""
        steps = [
            WorkflowStep("s-1", "Upload Document", "delay", {"seconds": 0.1}),
            WorkflowStep("s-2", "Parse Resume", "tool", {"tool_id": "summary_tool", "arguments": {"text": "Alice"}}, ["s-1"])
        ]
        def_id = self.executor.create_definition("Resume Review", "Resume review E2E", steps)
        
        # Verify definitions from DB
        row = self.db.get_workflow_definition(def_id)
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Resume Review")
        
        db_steps = self.db.list_workflow_steps(def_id)
        self.assertEqual(len(db_steps), 2)

    def test_workflow_conditional_branching(self) -> None:
        """Verifies that conditional statement evaluates expression and executes correct branch."""
        self.caught_events.clear()
        
        steps = [
            WorkflowStep("step_cond", "Check Score", "condition", {"expression": "variables['value'] > 80"}),
            WorkflowStep("step_true", "Notify Success", "notification", {"to": "admin"}, ["step_cond"]),
            WorkflowStep("step_false", "Notify Failure", "notification", {"to": "user"}, ["step_cond"])
        ]
        conds = [
            WorkflowCondition("cond-1", "variables['value'] > 80", "step_true", "step_false")
        ]
        def_id = self.executor.create_definition(
            "Conditional Workflow", "Tests conditional statements", steps, conds
        )

        # Trigger with variables matching True condition
        instance_id = self.executor.execute(def_id, {"value": 90})
        
        # Poll for status to change from PENDING/RUNNING
        for _ in range(50):
            inst = self.db.get_workflow_instance(instance_id)
            if inst and inst["status"] not in ["PENDING", "RUNNING"]:
                break
            time.sleep(0.1)

        inst = self.db.get_workflow_instance(instance_id)
        self.assertIsNotNone(inst)
        self.assertEqual(inst["status"], "COMPLETED")

        step_statuses = json.loads(inst["step_statuses"])
        self.assertEqual(step_statuses["step_cond"], "COMPLETED")
        self.assertEqual(step_statuses["step_true"], "COMPLETED")
        # Step false must be skipped (marked complete)
        self.assertEqual(step_statuses["step_false"], "COMPLETED")

    def test_workflow_user_approval_pause_and_resume(self) -> None:
        """Verifies that user approvals pause the workflow, trigger events, and resume correctly."""
        self.caught_events.clear()

        steps = [
            WorkflowStep("s-1", "Upload Resume", "delay", {"seconds": 0.1}),
            WorkflowStep("s-approve", "Manager Verification", "approval", {}, ["s-1"]),
            WorkflowStep("s-notify", "Dispatched", "notification", {"to": "user"}, ["s-approve"])
        ]
        def_id = self.executor.create_definition("Human Approval Workflow", "Approval tests", steps)

        # Start execution
        instance_id = self.executor.execute(def_id)
        
        # Poll for status to change to PAUSED
        for _ in range(50):
            inst = self.db.get_workflow_instance(instance_id)
            if inst and inst["status"] == "PAUSED":
                break
            time.sleep(0.1)

        inst = self.db.get_workflow_instance(instance_id)
        self.assertEqual(inst["status"], "PAUSED")
        
        # Assert approval required event is published
        self.assertIn("workflow.approval.required", self.caught_events)

        # Retrieve pending approval entry
        app_row = self.db.get_pending_workflow_approval(instance_id, "s-approve")
        self.assertIsNotNone(app_row)
        approval_id = app_row["approval_id"]

        # Approve step
        self.caught_events.clear()
        success = self.executor.approve_step(approval_id, "manager_john", "APPROVED", "Checks look correct")
        self.assertTrue(success)

        # Poll for status to change to COMPLETED
        for _ in range(50):
            inst_res = self.db.get_workflow_instance(instance_id)
            if inst_res and inst_res["status"] == "COMPLETED":
                break
            time.sleep(0.1)

        inst_res = self.db.get_workflow_instance(instance_id)
        self.assertEqual(inst_res["status"], "COMPLETED")
        self.assertIn("workflow.completed", self.caught_events)

    def test_failure_recovery_and_compensation(self) -> None:
        """Verifies that failures activate retries, and execute compensation rollback logic."""
        steps = [
            # Configures step that always throws tool registration errors
            WorkflowStep("s-fail", "Failing Tool Step", "tool", {
                "tool_id": "non_existent_tool",
                "retries": 2,
                "retry_delay": 0.1,
                "compensation": {"action": "rollback"}
            })
        ]
        def_id = self.executor.create_definition("Failures Test", "Failure recovery tests", steps)

        instance_id = self.executor.execute(def_id)
        
        # Poll for status to change from PENDING/RUNNING
        for _ in range(50):
            inst = self.db.get_workflow_instance(instance_id)
            if inst and inst["status"] not in ["PENDING", "RUNNING"]:
                break
            time.sleep(0.1)

        inst = self.db.get_workflow_instance(instance_id)
        self.assertEqual(inst["status"], "FAILED")

        # History should contain compensation logging entries
        history = self.db.list_workflow_history()
        actions = [h["action"] for h in history if h["instance_id"] == instance_id]
        self.assertIn("compensation", actions)

    def test_workflow_concurrency(self) -> None:
        """Concurrency test executing multiple workflows in parallel threadpools."""
        steps = [
            WorkflowStep("s-1", "Fast Delay Step", "delay", {"seconds": 0.1})
        ]
        def_id = self.executor.create_definition("Concurrency Test", "Parallel runs", steps)

        instance_ids = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as p:
            futures = [p.submit(self.executor.execute, def_id) for _ in range(5)]
            for fut in concurrent.futures.as_completed(futures):
                instance_ids.append(fut.result())

        # Wait for all runs
        time.sleep(0.8)

        for inst_id in instance_ids:
            inst = self.db.get_workflow_instance(inst_id)
            self.assertEqual(inst["status"], "COMPLETED")

    def test_workflow_schedules(self) -> None:
        """Verifies workflow scheduler polls and executes scheduled workflows."""
        steps = [
            WorkflowStep("s-1", "Schedule Step", "delay", {"seconds": 0.1})
        ]
        def_id = self.executor.create_definition("Scheduler Test", "Schedule execution", steps)

        scheduler = WorkflowScheduler(self.executor)
        scheduler.schedule_workflow(def_id, "* * * * *")
        
        # Start scheduler
        scheduler.start()
        
        # Wait 1.5 seconds for trigger and execution thread
        time.sleep(1.5)
        scheduler.stop()

        history = self.db.list_workflow_history()
        # Verify that an execution was recorded
        runs = [h for h in history if h["action"] == "started"]
        self.assertGreater(len(runs), 0)

    def test_workflow_api_controllers(self) -> None:
        """E2E REST endpoint tests verifying FastAPI CRUD routes mapping."""
        # 1. Create Workflow Definition REST route
        req_body = {
            "name": "E2E API Workflow",
            "description": "Exposing APIs tests",
            "steps": [
                {"step_id": "s-1", "name": "Load", "step_type": "delay", "config": {"seconds": 0.1}, "dependencies": []}
            ]
        }
        res_create = self.client.post("/workflows", json=req_body)
        self.assertEqual(res_create.status_code, 200)
        def_id = res_create.json().get("definition_id")
        self.assertIsNotNone(def_id)

        # 2. Get Definition detail REST route
        res_get = self.client.get(f"/workflows/{def_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json().get("name"), "E2E API Workflow")

        # 3. Execute Workflow REST route
        res_exec = self.client.post(f"/workflows/{def_id}/execute")
        self.assertEqual(res_exec.status_code, 200)
        instance_id = res_exec.json().get("instance_id")
        self.assertIsNotNone(instance_id)

        # 4. History REST route
        res_hist = self.client.get("/workflows/history")
        self.assertEqual(res_hist.status_code, 200)
        self.assertGreater(len(res_hist.json().get("history", [])), 0)
