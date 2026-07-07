"""Audit logger recording governance decisions and Matched Rules."""

from __future__ import annotations

import threading
import uuid
from typing import Dict, List, Optional

from backend.policy.models import AuditLogEntry, EvaluationResult


class AuditLogger:
    """Thread-safe persistent logger for policy evaluations and decisions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._logs: List[AuditLogEntry] = []

    def log(
        self,
        user_id: str,
        workspace_id: str,
        organization_id: str,
        action: str,
        context: Dict,
        evaluation: EvaluationResult,
    ) -> AuditLogEntry:
        """Appends a new audit log record to the persistent list."""
        entry = AuditLogEntry(
            audit_id=str(uuid.uuid4())[:8],
            user_id=user_id,
            workspace_id=workspace_id,
            organization_id=organization_id,
            action=action,
            context=context,
            evaluation=evaluation,
        )
        with self._lock:
            self._logs.append(entry)
        return entry

    def list_logs(self, workspace_id: Optional[str] = None) -> List[AuditLogEntry]:
        """Returns log entries, optionally filtered by workspace_id."""
        with self._lock:
            if workspace_id:
                return [log for log in self._logs if log.workspace_id == workspace_id]
            return list(self._logs)

    def clear(self) -> None:
        """Wipes the audit logs."""
        with self._lock:
            self._logs.clear()
