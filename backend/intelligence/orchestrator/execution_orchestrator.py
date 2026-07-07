"""Execution orchestrator coordinating selection, planning, optimization, and parallel run stages."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from backend.intelligence.contracts.request_models import IntelligenceRequest
from backend.intelligence.orchestrator.dependency_resolver import DependencyResolver
from backend.intelligence.orchestrator.execution_context import OrchestrationContext
from backend.intelligence.orchestrator.execution_policy import ExecutionPolicy, PolicyType
from backend.intelligence.orchestrator.models import OrchestratedResult
from backend.intelligence.orchestrator.module_selector import ModuleSelector
from backend.intelligence.orchestrator.parallel_executor import ParallelExecutor
from backend.intelligence.orchestrator.result_aggregator import ResultAggregator
from backend.intelligence.orchestrator.workflow_optimizer import WorkflowOptimizer
from backend.intelligence.orchestrator.workflow_planner import WorkflowPlanner
from backend.runtime.event import Event, EventBus, EventPriority, EventType

logger = logging.getLogger("nexus.orchestrator.engine")


class DynamicExecutionOrchestrator:
    """The dynamic cross-intelligence orchestrator engine."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._bus = event_bus or EventBus()
        self._selector = ModuleSelector()
        self._planner = WorkflowPlanner()
        self._executor = ParallelExecutor()

    def execute(
        self,
        request: IntelligenceRequest,
        policy_type: PolicyType = PolicyType.BALANCED,
        explicit_modules: Optional[List[str]] = None,
    ) -> OrchestratedResult:
        """Executes the dynamic cross-intelligence orchestration workflow.

        Args:
            request: The inbound IntelligenceRequest containing inputs and files.
            policy_type: The optimization policy (Fastest, Quality, Cost, Balanced).
            explicit_modules: Optional explicit selection list.

        Returns:
            OrchestratedResult with combined results, confidence, and timeline.
        """
        request_id = request.request_id

        # 1. Publish start event
        self._bus.publish(
            Event(
                event_type=EventType.ANALYSIS_STARTED,
                priority=EventPriority.NORMAL,
                payload={
                    "request_id": request_id,
                    "workspace_id": request.workspace_id,
                    "user_id": request.user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        )

        # 2. Select required modules
        selected_modules = self._selector.select_modules(
            query=request.input.get("query", ""),
            document_ids=[att.attachment_id for att in request.attachments],
            explicit_modules=explicit_modules,
        )

        # 3. Create execution plan
        policy = ExecutionPolicy(policy_type=policy_type)
        plan = self._planner.plan(selected_modules, policy)

        # 4. Optimize plan according to policy
        optimized_plan = WorkflowOptimizer.optimize(plan)

        # 5. Resolve dependencies & batch nodes topologically
        batches = DependencyResolver.resolve(optimized_plan.graph)

        self._bus.publish(
            Event(
                event_type=EventType.CUSTOM_EVENT,
                source="DynamicExecutionOrchestrator",
                payload={
                    "event": "orchestrator.plan.created",
                    "workspace_id": request.workspace_id,
                    "plan_id": optimized_plan.plan_id,
                    "batches": batches,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        )

        # 6. Initialize context
        ctx = OrchestrationContext(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            query=request.input.get("query", ""),
            document_ids=[att.attachment_id for att in request.attachments],
            session_id=request.session_id,
        )

        # 7. Run parallel executor
        self._executor.execute(optimized_plan.graph, batches, policy, ctx)

        # 8. Aggregate results
        result = ResultAggregator.aggregate(
            request_id=request_id,
            plan_id=optimized_plan.plan_id,
            graph=optimized_plan.graph,
            ctx=ctx,
        )

        # 9. Publish completion/failure events
        event_type = (
            EventType.ANALYSIS_COMPLETED
            if result.status == "completed"
            else EventType.ANALYSIS_FAILED
        )
        self._bus.publish(
            Event(
                event_type=event_type,
                priority=EventPriority.NORMAL,
                payload={
                    "request_id": request_id,
                    "orchestration_id": result.orchestration_id,
                    "status": result.status,
                    "modules": result.modules_executed,
                    "confidence": result.confidence_score,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        )

        return result
