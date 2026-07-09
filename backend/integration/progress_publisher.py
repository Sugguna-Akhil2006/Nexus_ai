"""Progress publisher — broadcasts live workflow progress to WebSocket connections.

Publishes ``FrontendEvent`` envelopes through the ``WebSocketManager``
so the frontend receives granular progress updates as each intelligence
module completes.  No business logic is performed here.
"""

from __future__ import annotations

import time
from typing import List, Optional

from backend.integration.frontend_contracts import (
    AnalysisCompletedEvent,
    AnalysisFailedEvent,
    FrontendEvent,
    ModuleCompletedEvent,
    ModuleStartedEvent,
    WorkflowEventKind,
    WorkflowProgressEvent,
    WorkflowStartedEvent,
)


class ProgressPublisher:
    """Emits structured progress events to the frontend via a WebSocket manager.

    Designed to be instantiated once per composition request and driven
    by the ``FrontendAdapter`` as it iterates through modules.

    Args:
        ws_manager: The ``WebSocketManager`` used to broadcast messages.
        request_id: Originating request identifier.
        workspace_id: Target workspace.
        modules: Ordered list of module names to be executed.
    """

    def __init__(
        self,
        ws_manager,          # WebSocketManager — typed loosely to avoid circular import
        request_id: str,
        workspace_id: str,
        modules: List[str],
    ) -> None:
        self._ws = ws_manager
        self._request_id = request_id
        self._workspace_id = workspace_id
        self._modules = modules
        self._total = len(modules)
        self._completed = 0
        self._started_at = time.monotonic()

    # ------------------------------------------------------------------
    # Lifecycle events
    # ------------------------------------------------------------------

    async def emit_started(self) -> None:
        """Broadcasts the ``workflow.started`` event."""
        evt = WorkflowStartedEvent(
            request_id=self._request_id,
            workspace_id=self._workspace_id,
            modules=self._modules,
            total_modules=self._total,
        )
        await self._broadcast(WorkflowEventKind.WORKFLOW_STARTED, evt.model_dump())

    async def emit_module_started(self, module: str, index: int) -> None:
        """Broadcasts ``module.started`` for the given module."""
        evt = ModuleStartedEvent(
            request_id=self._request_id,
            module=module,
            sequence_index=index,
        )
        await self._broadcast(WorkflowEventKind.MODULE_STARTED, evt.model_dump())

    async def emit_module_completed(
        self,
        module: str,
        confidence: float,
        duration_ms: float,
        finding_count: int = 0,
    ) -> None:
        """Broadcasts ``module.completed`` and updates aggregate progress."""
        self._completed += 1
        pct = (self._completed / self._total) * 100.0
        elapsed_ms = (time.monotonic() - self._started_at) * 1000.0

        mod_evt = ModuleCompletedEvent(
            request_id=self._request_id,
            module=module,
            confidence=confidence,
            duration_ms=duration_ms,
            finding_count=finding_count,
        )
        await self._broadcast(WorkflowEventKind.MODULE_COMPLETED, mod_evt.model_dump())

        prog_evt = WorkflowProgressEvent(
            request_id=self._request_id,
            completed_modules=self._completed,
            total_modules=self._total,
            percent_complete=round(pct, 1),
            current_module=module,
            elapsed_ms=round(elapsed_ms, 1),
        )
        await self._broadcast(WorkflowEventKind.WORKFLOW_PROGRESS, prog_evt.model_dump())

    async def emit_completed(self, evt: AnalysisCompletedEvent) -> None:
        """Broadcasts the final ``analysis.completed`` event."""
        await self._broadcast(WorkflowEventKind.ANALYSIS_COMPLETED, evt.model_dump())

    async def emit_failed(self, evt: AnalysisFailedEvent) -> None:
        """Broadcasts the ``analysis.failed`` event."""
        await self._broadcast(WorkflowEventKind.ANALYSIS_FAILED, evt.model_dump())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _broadcast(
        self,
        kind: WorkflowEventKind,
        payload: dict,
    ) -> None:
        envelope = FrontendEvent(
            kind=kind,
            request_id=self._request_id,
            workspace_id=self._workspace_id,
            payload=payload,
        )
        await self._ws.broadcast(self._workspace_id, envelope.model_dump())
