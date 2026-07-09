"""Trace service orchestrating RequestTrace capture and diagnostic logging."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

from backend.diagnostics.models import RequestTrace, TimelineStep
from backend.diagnostics.request_tracker import RequestTracker

logger = logging.getLogger("nexus.diagnostics.trace")


class TraceService:
    """Service coordinates logging of request traces and execution steps."""

    def __init__(self, request_tracker: RequestTracker) -> None:
        self._tracker = request_tracker

    def create_trace(
        self,
        request_id: str,
        workspace_id: str,
        user_id: str,
        modules_used: Optional[List[str]] = None,
        providers_used: Optional[List[str]] = None,
    ) -> RequestTrace:
        """Initializes a new request trace."""
        trace = RequestTrace(
            request_id=request_id,
            workspace_id=workspace_id,
            user_id=user_id,
            status="running",
            modules_used=modules_used or [],
            providers_used=providers_used or [],
            created_at=datetime.utcnow().isoformat(),
        )
        self._tracker.log_trace(trace)
        return trace

    def record_step(
        self,
        request_id: str,
        step: TimelineStep,
    ) -> None:
        """Appends an execution step to a request's timeline trace."""
        trace = self._tracker.get_trace(request_id)
        if trace:
            trace.timeline.append(step)
            # Add to modules if not present
            if step.step_type == "module" and step.step_name not in trace.modules_used:
                trace.modules_used.append(step.step_name)

    def complete_trace(
        self,
        request_id: str,
        duration_ms: float,
        retries: int = 0,
        errors: Optional[dict[str, str]] = None,
    ) -> None:
        """Sets trace state to completed with measured durations."""
        trace = self._tracker.get_trace(request_id)
        if trace:
            trace.status = "completed" if not errors else "failed"
            trace.duration_ms = round(duration_ms, 2)
            trace.retries = retries
            if errors:
                trace.errors.update(errors)
            self._tracker.log_trace(trace)
