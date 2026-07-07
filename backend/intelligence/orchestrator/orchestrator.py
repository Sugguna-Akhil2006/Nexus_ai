"""Main orchestrator coordinating intent detection, concurrency execution, and response synthesis."""

from datetime import datetime
from typing import Dict, List, Any
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.orchestrator.models import OrchestrationRequest, UnifiedIntelligenceResponse
from backend.intelligence.orchestrator.context_manager import OrchestrationContext
from backend.intelligence.orchestrator.request_analyzer import RequestAnalyzer
from backend.intelligence.orchestrator.module_selector import ModuleSelector
from backend.intelligence.orchestrator.execution_planner import ExecutionPlanner
from backend.intelligence.orchestrator.workflow_executor import WorkflowExecutor
from backend.intelligence.orchestrator.result_merger import ResultMerger
from backend.intelligence.orchestrator.response_formatter import ResponseFormatter


class CrossIntelligenceOrchestrator:
    """Central AI workflow coordinator for collaborative multi-module requests."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.analyzer = RequestAnalyzer()
        self.selector = ModuleSelector()
        self.planner = ExecutionPlanner()
        self.executor = WorkflowExecutor(db_path)
        self.merger = ResultMerger()
        self.formatter = ResponseFormatter()
        self.event_bus = EventBus()

    def orchestrate_request(self, req: OrchestrationRequest) -> UnifiedIntelligenceResponse:
        """Analyzes query intents, plans workflows, coordinates executions, and merges findings."""
        ctx = OrchestrationContext(req.workspace_id, req.query)
        
        # Publish orchestrator.started event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CrossIntelligenceOrchestrator",
            payload={
                "event": "orchestrator.started",
                "workspace_id": req.workspace_id,
                "query": req.query,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        # 1. Intent Detection
        intents = self.analyzer.analyze_request_intent(req.query)

        # 2. Capability Analysis / Module Selection
        selected_modules = self.selector.select_modules(intents, req.document_ids)

        # 3. Create Parallel/Sequential Execution Plan
        plan = self.planner.create_plan(selected_modules, req.options)
        
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CrossIntelligenceOrchestrator",
            payload={
                "event": "orchestrator.plan.created",
                "workspace_id": req.workspace_id,
                "plan_id": plan.plan_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        # 4. Execute Intelligence Modules
        evidence_list = self.executor.execute_plan(plan, req.workspace_id, req.user_id, req.document_ids, ctx)

        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CrossIntelligenceOrchestrator",
            payload={
                "event": "orchestrator.execution.completed",
                "workspace_id": req.workspace_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        # 5. Merge Results via Reasoning Engine
        reasoning_report = self.merger.merge_results(req.workspace_id, req.query, evidence_list, req.options)

        # 6. Format Unified Response
        timeline = ctx.get_timeline()
        modules_executed = [step.module_name for step in plan.steps]

        response = self.formatter.format_response(
            modules_executed=modules_executed,
            timeline=timeline,
            reasoning_report=reasoning_report
        )

        # Publish orchestrator.response.generated event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="CrossIntelligenceOrchestrator",
            payload={
                "event": "orchestrator.response.generated",
                "workspace_id": req.workspace_id,
                "response_id": response.response_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return response
