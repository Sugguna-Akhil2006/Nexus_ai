"""API gateway controller mapping capabilities to target modules and executing pipelines."""

import time
from typing import Optional

from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.core.registry import IntelligenceRegistry
from backend.intelligence.core.context import IntelligenceContext
from backend.api.intelligence.requests import GatewayExecutionRequest
from backend.api.intelligence.responses import GatewayExecutionResponse
from backend.api.intelligence.exceptions import ModuleNotFoundError, GatewayValidationError


class IntelligenceGateway:
    """Orchestrates request routing, input validation, context mapping, and event logs."""

    def __init__(self) -> None:
        self.registry = IntelligenceRegistry()
        self.event_bus = EventBus()

    def route_and_execute(self, request: GatewayExecutionRequest, timeout: Optional[float] = None) -> GatewayExecutionResponse:
        """Finds matching capability modules, maps inputs to context, and runs execution.

        Args:
            request: Standard Gateway request payload.
            timeout: Optional seconds threshold constraint.

        Returns:
            GatewayExecutionResponse: Gateway output payload.

        Raises:
            GatewayValidationError: On bad input.
            ModuleNotFoundError: On missing capability.
        """
        # Validate workspace_id
        if not request.workspace_id or not request.workspace_id.strip():
            raise GatewayValidationError("Workspace ID must not be empty.")

        # Publish Gateway Request event
        self._publish_event("gateway.request.received", request)

        # Match capabilities
        modules = self.registry.get_modules_by_capability(request.capability)
        if not modules:
            raise ModuleNotFoundError(request.capability)

        # Take first matching module
        module = modules[0]

        # Map to core IntelligenceContext
        context = IntelligenceContext(
            workspace_id=request.workspace_id,
            user_id=request.user_id,
            document_ids=request.document_ids,
            conversation_id=request.conversation_id,
            metadata=request.metadata
        )

        start = time.perf_counter()
        try:
            # Trigger module execution
            report = module.execute_workflow(context)
            duration = time.perf_counter() - start

            # Flatten warnings dictionary list
            flat_warnings = []
            for w_list in report.warnings.values():
                flat_warnings.extend(w_list)

            return GatewayExecutionResponse(
                status=report.status,
                execution_id=report.execution_id,
                module=report.module_name,
                execution_time=round(duration, 4),
                data=report.stage_results,
                warnings=flat_warnings,
                errors=report.errors,
                telemetry=report.metrics
            )
        except Exception as e:
            # Log failed execution
            duration = time.perf_counter() - start
            return GatewayExecutionResponse(
                status="failed",
                execution_id="exec-error",
                module=module.name,
                execution_time=round(duration, 4),
                data={},
                warnings=[],
                errors={"GatewayError": str(e)},
                telemetry={}
            )

    def _publish_event(self, event_name: str, request: GatewayExecutionRequest) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="IntelligenceGateway",
            payload={
                "event": event_name,
                "workspace_id": request.workspace_id,
                "capability": request.capability
            }
        )
        self.event_bus.publish(event)
