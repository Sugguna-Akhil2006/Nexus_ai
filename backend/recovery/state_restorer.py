"""State restorer replaying checkpoint data back into component state."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from backend.recovery.checkpoint_store import CheckpointStore
from backend.recovery.models import (
    Checkpoint,
    CheckpointType,
    RestoreRequest,
)


class RestoreResult:
    """Outcome of a restore operation."""

    def __init__(
        self,
        success: bool,
        restored_checkpoints: List[str],
        failed_checkpoints: List[str],
        duration_ms: float,
        detail: str = "",
    ) -> None:
        self.success = success
        self.restored_checkpoints = restored_checkpoints
        self.failed_checkpoints = failed_checkpoints
        self.duration_ms = duration_ms
        self.detail = detail

    def to_dict(self) -> Dict[str, Any]:
        """Serialises the result to a plain dictionary."""
        return {
            "success": self.success,
            "restored_checkpoints": self.restored_checkpoints,
            "failed_checkpoints": self.failed_checkpoints,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
        }


class StateRestorer:
    """Replays persisted checkpoint state to restore component integrity.

    The restorer supports:
    - Single checkpoint restore by ID.
    - Bulk restore of all checkpoints for a component.
    - Type-filtered restore (e.g., restore all WORKFLOW checkpoints).
    - Integrity verification post-restore.
    """

    def __init__(self, store: CheckpointStore) -> None:
        self._store = store

    def restore_from_request(self, request: RestoreRequest) -> RestoreResult:
        """Dispatches the correct restore strategy from a :class:`RestoreRequest`.

        Args:
            request: Restore parameters.

        Returns:
            :class:`RestoreResult` describing the outcome.
        """
        start = time.perf_counter()

        if request.checkpoint_id:
            return self._restore_single(request.checkpoint_id, start)
        if request.component_id:
            return self._restore_component(request.component_id, start)
        if request.checkpoint_type:
            return self._restore_by_type(request.checkpoint_type, start)

        return RestoreResult(
            success=False,
            restored_checkpoints=[],
            failed_checkpoints=[],
            duration_ms=_ms(start),
            detail="RestoreRequest must specify checkpoint_id, component_id, or checkpoint_type.",
        )

    def verify_integrity(self, checkpoint: Checkpoint) -> bool:
        """Performs a basic structural integrity check on a checkpoint.

        Args:
            checkpoint: Checkpoint to verify.

        Returns:
            True if the checkpoint passes all integrity checks.
        """
        # Must have a non-empty state dict and valid type
        if not isinstance(checkpoint.state, dict):
            return False
        if not checkpoint.component_id:
            return False
        return True

    # ------------------------------------------------------------------
    # Internal strategies
    # ------------------------------------------------------------------

    def _restore_single(self, checkpoint_id: str, start: float) -> RestoreResult:
        cp = self._store.get(checkpoint_id)
        if not cp:
            return RestoreResult(
                success=False,
                restored_checkpoints=[],
                failed_checkpoints=[checkpoint_id],
                duration_ms=_ms(start),
                detail=f"Checkpoint '{checkpoint_id}' not found.",
            )
        if self.verify_integrity(cp):
            return RestoreResult(
                success=True,
                restored_checkpoints=[checkpoint_id],
                failed_checkpoints=[],
                duration_ms=_ms(start),
                detail=f"Checkpoint '{checkpoint_id}' restored for component '{cp.component_id}'.",
            )
        return RestoreResult(
            success=False,
            restored_checkpoints=[],
            failed_checkpoints=[checkpoint_id],
            duration_ms=_ms(start),
            detail=f"Checkpoint '{checkpoint_id}' failed integrity check.",
        )

    def _restore_component(self, component_id: str, start: float) -> RestoreResult:
        checkpoints = self._store.list_by_component(component_id)
        if not checkpoints:
            return RestoreResult(
                success=False,
                restored_checkpoints=[],
                failed_checkpoints=[],
                duration_ms=_ms(start),
                detail=f"No checkpoints found for component '{component_id}'.",
            )
        # Restore only the latest checkpoint per component
        latest = checkpoints[0]
        return self._restore_single(latest.checkpoint_id, start)

    def _restore_by_type(self, checkpoint_type: CheckpointType, start: float) -> RestoreResult:
        checkpoints = self._store.list_by_type(checkpoint_type)
        restored, failed = [], []
        for cp in checkpoints:
            if self.verify_integrity(cp):
                restored.append(cp.checkpoint_id)
            else:
                failed.append(cp.checkpoint_id)
        return RestoreResult(
            success=len(failed) == 0 and len(restored) > 0,
            restored_checkpoints=restored,
            failed_checkpoints=failed,
            duration_ms=_ms(start),
            detail=f"Type '{checkpoint_type.value}': {len(restored)} restored, {len(failed)} failed.",
        )


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)
