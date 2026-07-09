"""Diagnostic manager providing unified facade access to traces, logs, and metrics."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from backend.diagnostics.error_analyzer import ErrorAnalyzer
from backend.diagnostics.execution_history import ExecutionHistory
from backend.diagnostics.models import ErrorRecord, RequestTrace, TimelineStep
from backend.diagnostics.provider_tracker import ProviderTracker
from backend.diagnostics.request_tracker import RequestTracker
from backend.diagnostics.trace_service import TraceService
from backend.diagnostics.workflow_tracker import WorkflowTracker


class DiagnosticManager:
    """The central coordinator (facade) for all diagnostics and tracing operations."""

    _instance: Optional["DiagnosticManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "DiagnosticManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        self.request_tracker = RequestTracker()
        self.provider_tracker = ProviderTracker()
        self.workflow_tracker = WorkflowTracker()
        self.trace_service = TraceService(self.request_tracker)
        self.history = ExecutionHistory(db_path)
        self._initialized = True

    # ------------------------------------------------------------------
    # Request lifecycle hooks
    # ------------------------------------------------------------------

    def start_request(
        self,
        request_id: str,
        workspace_id: str,
        user_id: str,
    ) -> RequestTrace:
        """Starts tracing for a new request."""
        return self.trace_service.create_trace(request_id, workspace_id, user_id)

    def log_step(
        self,
        request_id: str,
        step_name: str,
        step_type: str,
        duration_ms: float,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Appends a completed timeline milestone step to a request trace."""
        step = TimelineStep(
            step_name=step_name,
            step_type=step_type,
            status=status,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )
        self.trace_service.record_step(request_id, step)

    def fail_request(
        self,
        request_id: str,
        error: Exception,
        duration_ms: float,
        module_name: Optional[str] = None,
    ) -> None:
        """Records a request failure, logs the error, and completes the trace."""
        err_record = ErrorAnalyzer.classify(request_id, error, module_name)
        err_dict = {module_name or "request": err_record.message}
        self.trace_service.complete_trace(
            request_id=request_id,
            duration_ms=duration_ms,
            errors=err_dict,
        )
        # Save final state to persistence
        trace = self.request_tracker.get_trace(request_id)
        if trace:
            self.history.save_trace(trace)

    def complete_request(
        self,
        request_id: str,
        duration_ms: float,
        retries: int = 0,
    ) -> None:
        """Completes a request trace and saves it to SQLite history."""
        self.trace_service.complete_trace(
            request_id=request_id,
            duration_ms=duration_ms,
            retries=retries,
        )
        trace = self.request_tracker.get_trace(request_id)
        if trace:
            self.history.save_trace(trace)
