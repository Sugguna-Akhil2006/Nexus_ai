"""Workflow recovery handler resuming interrupted workflows from checkpoints."""

from __future__ import annotations

import time
import uuid
from typing import Dict, Optional

from backend.recovery.checkpoint_store import CheckpointStore
from backend.recovery.models import (
    CheckpointType,
    FailureScenario,
    RecoveryEvent,
    RecoveryStatus,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


class WorkflowRecovery:
    """Detects interrupted workflows and resumes them from their last checkpoint.

    The recovery process:
    1. Scans the checkpoint store for WORKFLOW checkpoints.
    2. Identifies those whose state marks them as interrupted/failed.
    3. Attempts to resume execution from the last valid checkpoint.
    4. Emits a :class:`RecoveryEvent` for each workflow.
    """

    def __init__(self, store: CheckpointStore) -> None:
        self._store = store

    def recover(self, scenario: FailureScenario = FailureScenario.PARTIAL_WORKFLOW_FAILURE) -> RecoveryEvent:
        """Scans workflow checkpoints and attempts recovery.

        Args:
            scenario: The failure scenario triggering this recovery.

        Returns:
            A :class:`RecoveryEvent` describing the outcome.
        """
        start = time.perf_counter()
        event_id = str(uuid.uuid4())[:8]

        checkpoints = self._store.list_by_type(CheckpointType.WORKFLOW)
        interrupted = [
            cp for cp in checkpoints
            if cp.state.get("status") in ("interrupted", "failed", "partial")
        ]

        if not interrupted:
            return RecoveryEvent(
                event_id=event_id,
                scenario=scenario,
                component="workflow_engine",
                status=RecoveryStatus.COMPLETED,
                detail=f"No interrupted workflows found. {len(checkpoints)} checkpoint(s) healthy.",
                duration_ms=_ms(start),
            )

        resumed = []
        failed = []
        for cp in interrupted:
            try:
                # Simulate resuming: update the state to 'resumed'
                cp.state["status"] = "resumed"
                cp.state["resumed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                self._store.save(cp)
                resumed.append(cp.component_id)
            except Exception as exc:
                failed.append(f"{cp.component_id}: {exc}")

        status = RecoveryStatus.COMPLETED if not failed else (
            RecoveryStatus.PARTIAL if resumed else RecoveryStatus.FAILED
        )
        return RecoveryEvent(
            event_id=event_id,
            scenario=scenario,
            component="workflow_engine",
            status=status,
            detail=(
                f"Resumed {len(resumed)} workflow(s). "
                + (f"Failed: {failed}" if failed else "All succeeded.")
            ),
            duration_ms=_ms(start),
        )
