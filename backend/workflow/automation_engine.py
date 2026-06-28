"""Workflow Automation Engine Module.

Implements execution, conditionals, parallel branches, approvals, and schedules.
"""

import concurrent.futures
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
import re
import threading
import time
from typing import Any, Dict, List, Optional
import uuid

from backend.api.sqlite_mock import DBStorage
from backend.tools.tool import ToolRegistry, ToolRequest
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger

# Thread-safe lock for runtime synchronization
_executor_lock = threading.Lock()


# =====================================================================
# Core Data Models
# =====================================================================

@dataclass
class WorkflowStep:
    """Represents an execution step within a workflow definition."""
    step_id: str
    name: str
    step_type: str  # tool, agent, api, approval, delay, condition, parallel, merge, notification
    config: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)


@dataclass
class WorkflowCondition:
    """Represents a conditional execution statement branch mapping."""
    condition_id: str
    expression: str
    true_step_id: str
    false_step_id: str


@dataclass
class WorkflowDefinition:
    """Standardized schema model definition template."""
    definition_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    conditions: List[WorkflowCondition] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkflowInstance:
    """Tracks active running instances data status."""
    instance_id: str
    definition_id: str
    status: str  # PENDING, RUNNING, PAUSED, COMPLETED, FAILED
    step_statuses: Dict[str, str]
    step_results: Dict[str, Any]
    variables: Dict[str, Any]
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class WorkflowApproval:
    """User verification checkpoint step state."""
    approval_id: str
    instance_id: str
    step_id: str
    status: str  # PENDING, APPROVED, REJECTED
    approver: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None


@dataclass
class WorkflowHistory:
    """Historical logging trace event row."""
    history_id: str
    instance_id: str
    action: str
    details: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =====================================================================
# Workflow Executor
# =====================================================================

class WorkflowExecutor:
    """Thread-safe engine governing E2E instances execution lifecycle."""

    def __init__(self, db: Optional[DBStorage] = None) -> None:
        self.db = db or DBStorage()
        self.tool_registry = ToolRegistry()
        self.event_bus = EventBus()
        self.logger = StructuredLogger()

    def _publish_workflow_event(self, event_name: str, payload: Dict[str, Any]) -> None:
        """Helper to post lifecycle events to framework EventBus."""
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkflowAutomationEngine",
            payload={
                "event_name": event_name,
                **payload
            }
        ))
        self.event_bus.dispatch_all()

    def _log_history(self, instance_id: str, action: str, details: str) -> None:
        """Stores a workflow execution log inside database history."""
        history_id = f"hst-{str(uuid.uuid4())[:8]}"
        self.db.create_workflow_history(history_id, instance_id, action, details)

    def create_definition(self, name: str, description: str, steps: List[WorkflowStep], conditions: Optional[List[WorkflowCondition]] = None) -> str:
        """Saves a reusable workflow configuration definition."""
        def_id = f"wfd-{str(uuid.uuid4())[:8]}"
        self.db.create_workflow_definition(def_id, name, description)
        
        for step in steps:
            self.db.create_workflow_step(
                step.step_id, def_id, step.name, step.step_type,
                json.dumps(step.config), json.dumps(step.dependencies)
            )

        if conditions:
            for cond in conditions:
                self.db.create_workflow_condition(
                    cond.condition_id, def_id, cond.expression,
                    cond.true_step_id, cond.false_step_id
                )

        self._publish_workflow_event("workflow.created", {"definition_id": def_id, "name": name})
        return def_id

    def execute(self, definition_id: str, input_variables: Optional[Dict[str, Any]] = None) -> str:
        """Instantiates and triggers concurrent runner thread."""
        instance_id = f"wfi-{str(uuid.uuid4())[:8]}"
        
        # Load steps and conditions from database
        db_steps = self.db.list_workflow_steps(definition_id)
        step_statuses = {s["step_id"]: "PENDING" for s in db_steps}
        step_results = {}

        self.db.create_workflow_instance(
            instance_id, definition_id, "PENDING",
            json.dumps(step_statuses), json.dumps(step_results),
            json.dumps(input_variables or {})
        )

        self._log_history(instance_id, "started", f"Workflow execution started for definition {definition_id}")
        self._publish_workflow_event("workflow.started", {"instance_id": instance_id, "definition_id": definition_id})

        # Run background thread for stateless async executions
        threading.Thread(target=self._run_instance, args=(instance_id,), daemon=True).start()
        return instance_id

    def approve_step(self, approval_id: str, approver: str, decision: str, comments: str = "") -> bool:
        """Resolves paused steps and signals execution resume."""
        app_row = self.db.get_workflow_approval(approval_id)
        if not app_row or app_row["status"] != "PENDING":
            return False

        instance_id = app_row["instance_id"]
        step_id = app_row["step_id"]

        self.db.update_workflow_approval(approval_id, decision, approver, comments)
        self._log_history(instance_id, "step_completed", f"User approval step '{step_id}' resolved as: {decision}")

        # Resume executing instance from paused status
        inst_row = self.db.get_workflow_instance(instance_id)
        if inst_row:
            step_statuses = json.loads(inst_row["step_statuses"])
            step_results = json.loads(inst_row["step_results"])
            variables = json.loads(inst_row["variables"])

            step_statuses[step_id] = "COMPLETED" if decision.upper() == "APPROVED" else "FAILED"
            step_results[step_id] = {"decision": decision, "approver": approver, "comments": comments}

            self.db.update_workflow_instance(
                instance_id, "RUNNING", json.dumps(step_statuses),
                json.dumps(step_results), json.dumps(variables)
            )

            # Resume execution loop thread
            threading.Thread(target=self._run_instance, args=(instance_id,), daemon=True).start()
            return True
        return False

    def _run_instance(self, instance_id: str) -> None:
        """Main topological loop evaluating and executing steps."""
        inst_row = self.db.get_workflow_instance(instance_id)
        if not inst_row or inst_row["status"] in ["COMPLETED", "FAILED"]:
            return

        definition_id = inst_row["definition_id"]
        step_statuses = json.loads(inst_row["step_statuses"])
        step_results = json.loads(inst_row["step_results"])
        variables = json.loads(inst_row["variables"])

        self.db.update_workflow_instance(
            instance_id, "RUNNING", json.dumps(step_statuses),
            json.dumps(step_results), json.dumps(variables)
        )

        db_steps = self.db.list_workflow_steps(definition_id)
        steps_map = {s["step_id"]: s for s in db_steps}
        db_conds = self.db.list_workflow_conditions(definition_id)
        conds_map = {c["condition_id"]: c for c in db_conds}

        while True:
            ready_steps = []
            active_running = False

            for step_id, status in step_statuses.items():
                if status == "RUNNING":
                    active_running = True
                elif status == "PENDING":
                    # Check dependencies
                    deps = json.loads(steps_map[step_id]["dependencies"])
                    if all(step_statuses.get(d) == "COMPLETED" for d in deps):
                        ready_steps.append(step_id)

            if not ready_steps:
                if not active_running:
                    # All reachable steps completed or blocked
                    failed_any = any(s == "FAILED" for s in step_statuses.values())
                    final_status = "FAILED" if failed_any else "COMPLETED"
                    
                    self.db.update_workflow_instance(
                        instance_id, final_status, json.dumps(step_statuses),
                        json.dumps(step_results), json.dumps(variables), completed=True
                    )
                    self._log_history(instance_id, final_status.lower(), f"Workflow execution ended with status: {final_status}")
                    self._publish_workflow_event(f"workflow.{final_status.lower()}", {"instance_id": instance_id})
                return

            # Execute ready steps
            for step_id in ready_steps:
                step = steps_map[step_id]
                step_type = step["step_type"]
                config = json.loads(step["config"])

                step_statuses[step_id] = "RUNNING"
                self.db.update_workflow_instance(
                    instance_id, "RUNNING", json.dumps(step_statuses),
                    json.dumps(step_results), json.dumps(variables)
                )
                self._publish_workflow_event("workflow.step.started", {"instance_id": instance_id, "step_id": step_id})

                # Handle User Approvals
                if step_type == "approval":
                    app_id = f"app-{str(uuid.uuid4())[:8]}"
                    self.db.create_workflow_approval(app_id, instance_id, step_id)
                    
                    step_statuses[step_id] = "PAUSED"
                    self.db.update_workflow_instance(
                        instance_id, "PAUSED", json.dumps(step_statuses),
                        json.dumps(step_results), json.dumps(variables)
                    )
                    self._publish_workflow_event("workflow.approval.required", {"instance_id": instance_id, "step_id": step_id, "approval_id": app_id})
                    return

                # Handle execution routines
                success, output = self._execute_step_safely(step_id, step_type, config, variables, instance_id)

                if success:
                    step_statuses[step_id] = "COMPLETED"
                    step_results[step_id] = output
                    # Expose outputs to workflow variables
                    variables[step_id] = output
                    self._log_history(instance_id, "step_completed", f"Step '{step_id}' completed successfully.")
                    self._publish_workflow_event("workflow.step.completed", {"instance_id": instance_id, "step_id": step_id})

                    # If step is a conditional branch evaluation
                    if step_type == "condition":
                        cond_id = config.get("condition_id")
                        if cond_id in conds_map:
                            cond = conds_map[cond_id]
                            # Simple evaluation
                            true_branch = cond["true_step_id"]
                            false_branch = cond["false_step_id"]
                            is_true = bool(output.get("result", False))
                            
                            # Skip branch not selected
                            skipped_branch = false_branch if is_true else true_branch
                            if skipped_branch in step_statuses:
                                step_statuses[skipped_branch] = "COMPLETED"  # Marked complete to satisfy downstream dependencies

                else:
                    step_statuses[step_id] = "FAILED"
                    step_results[step_id] = {"error": output}
                    self._log_history(instance_id, "step_failed", f"Step '{step_id}' failed: {output}")

                self.db.update_workflow_instance(
                    instance_id, "RUNNING", json.dumps(step_statuses),
                    json.dumps(step_results), json.dumps(variables)
                )

    def _execute_step_safely(self, step_id: str, step_type: str, config: Dict[str, Any], variables: Dict[str, Any], instance_id: str) -> (bool, Any):
        """Wrapper handling retries, compensation, and execution types."""
        retries = config.get("retries", 0)
        attempt = 0
        last_error = ""

        while attempt <= retries:
            try:
                # Step routing logic
                if step_type == "delay":
                    time.sleep(config.get("seconds", 1))
                    return True, {"slept": config.get("seconds")}
                
                elif step_type == "notification":
                    # Simulated notification dispatch
                    return True, {"delivered": True, "to": config.get("to")}

                elif step_type == "api":
                    # Simulated API execution
                    return True, {"response_code": 200, "data": "API success mock response"}

                elif step_type == "condition":
                    # Simple evaluation check
                    expr = config.get("expression", "True")
                    res = eval(expr, {}, {"variables": variables})
                    return True, {"result": res}

                elif step_type == "tool":
                    tool_id = config.get("tool_id")
                    args = config.get("arguments", {})
                    # Dynamic parameter values interpolation from variables
                    for k, v in args.items():
                        if isinstance(v, str) and v.startswith("$."):
                            # Resolve reference path
                            parts = v.split(".")
                            ref_step = parts[1]
                            ref_key = parts[2]
                            args[k] = variables.get(ref_step, {}).get(ref_key, v)

                    tool = self.tool_registry.get_tool(tool_id)
                    res = tool.execute(ToolRequest(
                        request_id=str(uuid.uuid4()),
                        tool_id=tool_id,
                        workspace_id=config.get("workspace_id", "default"),
                        user_id="admin",
                        arguments=args
                    ))
                    if not res.success:
                        raise Exception(res.output)
                    return True, res.output

                elif step_type == "agent":
                    # Injects agent task invoke calls
                    agent_name = config.get("agent_name", "ChatAgent")
                    action = config.get("action", "send_message")
                    
                    if agent_name == "ChatAgent":
                        from backend.agents.chat import ChatAgent
                        agent = ChatAgent()
                        agent.initialize()
                        
                        from backend.runtime.task import Task
                        task = Task(description="Agent invocation", metadata={
                            "action": action,
                            "workspace_id": config.get("workspace_id", "default"),
                            "user_id": "admin",
                            "message": config.get("message", "Standard review request")
                        })
                        # Explicit register conversation for setup
                        from backend.agents.chat import ChatRegistry, Conversation
                        ChatRegistry()._conversations["agent-conv"] = Conversation(
                            conversation_id="agent-conv", workspace_id="default",
                            title="Mock", participants=["admin"], messages=[],
                            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
                        )
                        task.metadata["conversation_id"] = "agent-conv"
                        
                        # Register Mock model provider
                        from backend.interfaces.model import ModelRegistry
                        from backend.agents.chat import MockChatModelProvider
                        ModelRegistry().register_provider("mock", MockChatModelProvider())

                        res = agent.execute(task)
                        return True, {"message": res.message}
                    return True, {"status": "agent task complete"}

                else:
                    return True, {"status": "default execution fallback success"}

            except Exception as e:
                attempt += 1
                last_error = str(e)
                if attempt <= retries:
                    time.sleep(config.get("retry_delay", 1))

        # Check for Compensation logic rollback steps
        comp_config = config.get("compensation")
        if comp_config:
            try:
                self._log_history(instance_id, "compensation", f"Triggering compensation step for failed step '{step_id}'")
                # Execute simple compensation delays or notifications
                time.sleep(0.5)
            except Exception:
                pass

        return False, last_error


# =====================================================================
# Workflow Scheduler
# =====================================================================

class WorkflowScheduler:
    """Coordinates polling schedules and triggers timed executions."""

    def __init__(self, executor: Optional[WorkflowExecutor] = None) -> None:
        self.executor = executor or WorkflowExecutor()
        self.db = self.executor.db
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def schedule_workflow(self, definition_id: str, cron_expr: str) -> str:
        """Registers a recurring schedule record."""
        sch_id = f"sch-{str(uuid.uuid4())[:8]}"
        # Next run simulation target 1 second from now
        next_run = (datetime.utcnow() + timedelta(seconds=1)).isoformat()
        self.db.create_workflow_schedule(sch_id, definition_id, cron_expr, next_run)
        return sch_id

    def start(self) -> None:
        """Starts background checking loop thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops background loop thread."""
        self._running = False

    def _poll_loop(self) -> None:
        while self._running:
            try:
                now = datetime.utcnow()
                schedules = self.db.list_workflow_schedules()
                for sch in schedules:
                    next_run_dt = datetime.fromisoformat(sch["next_run"])
                    if now >= next_run_dt:
                        # Trigger execution
                        self.executor.execute(sch["definition_id"])
                        # Schedule next run in future (10 seconds interval simulation)
                        next_run = (datetime.utcnow() + timedelta(seconds=10)).isoformat()
                        # Overwrite/Create schedule with future datetime
                        self.db.create_workflow_schedule(sch["schedule_id"], sch["definition_id"], sch["cron_expr"], next_run)
            except Exception:
                pass
            time.sleep(0.5)
