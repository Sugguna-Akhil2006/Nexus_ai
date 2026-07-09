"""Audit manager writing and storing AI workflow and policy audit events."""

from __future__ import annotations

import threading
import uuid
from typing import Dict, List, Optional

from backend.governance.models import AuditTrailEntry


class AuditManager:
    """Thread-safe auditor recording operational event context history logs."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: List[AuditTrailEntry] = []

    def record_event(
        self,
        category: str,
        actor: str,
        action: str,
        context: Optional[Dict] = None,
    ) -> AuditTrailEntry:
        """Appends a new event audit record."""
        entry = AuditTrailEntry(
            audit_id=str(uuid.uuid4())[:8],
            category=category,
            actor=actor,
            action=action,
            context=context or {},
        )
        with self._lock:
            self._entries.append(entry)
        return entry

    def list_history(self, category: Optional[str] = None) -> List[AuditTrailEntry]:
        """Lists audit history records, optionally filtered by category."""
        with self._lock:
            if category:
                return [e for e in self._entries if e.category == category]
            return list(self._entries)

    def clear(self) -> None:
        """Wipes the audit history log list."""
        with self._lock:
            self._entries.clear()
