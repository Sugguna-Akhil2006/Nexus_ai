"""Data retention manager truncating expired history logs."""

from __future__ import annotations

from typing import List

from backend.governance.models import AuditTrailEntry


class RetentionManager:
    """Manages truncation rules for historical log entries."""

    @staticmethod
    def enforce_retention(logs: List[AuditTrailEntry], max_count: int = 100) -> List[AuditTrailEntry]:
        """Truncates historical entries exceeding the max retention length."""
        if len(logs) <= max_count:
            return logs
        # Retain only the most recent logs
        return logs[-max_count:]
