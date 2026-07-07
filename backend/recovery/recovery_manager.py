"""Central recovery manager orchestrating checkpoints, backups, and restore operations."""

from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.recovery.backup_scheduler import BackupScheduler
from backend.recovery.checkpoint_store import CheckpointStore
from backend.recovery.health_recovery import HealthRecovery
from backend.recovery.models import (
    BackupRecord,
    BackupType,
    Checkpoint,
    CheckpointType,
    FailureScenario,
    RecoveryRun,
    RecoveryStatus,
    RestoreRequest,
)
from backend.recovery.provider_recovery import ProviderRecovery
from backend.recovery.recovery_report import RecoveryReport
from backend.recovery.snapshot_manager import SnapshotManager
from backend.recovery.state_restorer import StateRestorer
from backend.recovery.workflow_recovery import WorkflowRecovery


class RecoveryManager:
    """Thread-safe singleton orchestrating all disaster recovery operations.

    Responsibilities:
    - Accept new checkpoints from platform components.
    - Trigger backup snapshots (manual or scheduled).
    - Execute restore workflows against the checkpoint store.
    - Coordinate scenario-specific recovery handlers.
    - Maintain a full history of all recovery runs.
    """

    _instance: Optional["RecoveryManager"] = None

    def __new__(cls) -> "RecoveryManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_ready", False):
            return

        # Isolated snapshot directory inside backend/recovery/
        _base = os.path.dirname(os.path.abspath(__file__))
        _snap_dir = os.path.join(_base, ".snapshots")

        self._lock = threading.RLock()
        self._store = CheckpointStore(db_path=":memory:")
        self._snapshots = SnapshotManager(self._store, snapshot_dir=_snap_dir)
        self._restorer = StateRestorer(self._store)
        self._history: List[RecoveryRun] = []
        self._ready = True

    # ------------------------------------------------------------------
    # Checkpointing
    # ------------------------------------------------------------------

    def save_checkpoint(
        self,
        checkpoint_type: CheckpointType,
        component_id: str,
        state: Dict,
        metadata: Optional[Dict] = None,
    ) -> Checkpoint:
        """Persists a component state checkpoint.

        Args:
            checkpoint_type: Category of checkpoint.
            component_id: Owning component identifier.
            state: State dictionary to persist.
            metadata: Optional extra metadata.

        Returns:
            Created :class:`Checkpoint`.
        """
        cp = Checkpoint(
            checkpoint_id=CheckpointStore.generate_id(),
            checkpoint_type=checkpoint_type,
            component_id=component_id,
            state=state,
            metadata=metadata or {},
        )
        self._store.save(cp)
        return cp

    def list_checkpoints(self, component_id: Optional[str] = None) -> List[Checkpoint]:
        """Lists checkpoints, optionally filtered by component."""
        if component_id:
            return self._store.list_by_component(component_id)
        return self._store.list_all()

    # ------------------------------------------------------------------
    # Backup
    # ------------------------------------------------------------------

    def backup(self, backup_type: BackupType = BackupType.FULL) -> BackupRecord:
        """Triggers a backup snapshot of the specified type.

        Args:
            backup_type: Strategy to apply.

        Returns:
            :class:`BackupRecord`.
        """
        if backup_type == BackupType.INCREMENTAL:
            return self._snapshots.take_incremental_backup()
        if backup_type == BackupType.METADATA:
            return self._snapshots.take_metadata_backup()
        return self._snapshots.take_full_backup()

    def list_backups(self) -> List[BackupRecord]:
        """Returns all backup records."""
        return self._snapshots.list_backups()

    # ------------------------------------------------------------------
    # Restore
    # ------------------------------------------------------------------

    def restore(self, request: RestoreRequest) -> Dict:
        """Executes a restore operation from a checkpoint or backup.

        Args:
            request: Restore parameters.

        Returns:
            Result dictionary with success, detail, and duration.
        """
        result = self._restorer.restore_from_request(request)
        return result.to_dict()

    # ------------------------------------------------------------------
    # Scenario recovery
    # ------------------------------------------------------------------

    def recover(self, scenario: FailureScenario) -> RecoveryRun:
        """Runs the scenario-specific recovery pipeline.

        Args:
            scenario: The failure type to recover from.

        Returns:
            Completed :class:`RecoveryRun` with full timeline.
        """
        with self._lock:
            run_id = str(uuid.uuid4())[:8]
            started = datetime.now(timezone.utc).isoformat()
            t_start = time.perf_counter()

            run = RecoveryRun(
                run_id=run_id,
                scenario=scenario,
                started_at=started,
                status=RecoveryStatus.IN_PROGRESS,
            )

            # Always run health probe
            health_event = HealthRecovery().recover(scenario)
            run.timeline.append(health_event)

            # Scenario-specific handlers
            if scenario in (
                FailureScenario.PARTIAL_WORKFLOW_FAILURE,
                FailureScenario.WORKER_CRASH,
            ):
                wf_event = WorkflowRecovery(self._store).recover(scenario)
                run.timeline.append(wf_event)

            if scenario in (
                FailureScenario.PROVIDER_FAILURE,
                FailureScenario.NETWORK_INTERRUPTION,
            ):
                prov_event = ProviderRecovery().recover(scenario)
                run.timeline.append(prov_event)

            # Determine final status
            statuses = {ev.status for ev in run.timeline}
            if RecoveryStatus.FAILED in statuses:
                run.status = RecoveryStatus.PARTIAL if RecoveryStatus.COMPLETED in statuses else RecoveryStatus.FAILED
                run.failed_components = [
                    ev.component for ev in run.timeline if ev.status == RecoveryStatus.FAILED
                ]
            else:
                run.status = RecoveryStatus.COMPLETED

            run.recovered_components = [
                ev.component
                for ev in run.timeline
                if ev.status in (RecoveryStatus.COMPLETED, RecoveryStatus.PARTIAL)
            ]
            run.completed_at = datetime.now(timezone.utc).isoformat()
            run.duration_ms = round((time.perf_counter() - t_start) * 1000, 2)
            run.integrity_verified = run.status == RecoveryStatus.COMPLETED

            self._history.append(run)
            return run

    # ------------------------------------------------------------------
    # History and reporting
    # ------------------------------------------------------------------

    def get_history(self) -> List[RecoveryRun]:
        """Returns all past recovery runs."""
        with self._lock:
            return list(self._history)

    def get_latest(self) -> Optional[RecoveryRun]:
        """Returns the most recent recovery run."""
        with self._lock:
            return self._history[-1] if self._history else None

    def generate_report(self, fmt: str = "markdown") -> str:
        """Generates a report for the latest recovery run.

        Args:
            fmt: ``"markdown"``, ``"json"``, or ``"html"``.

        Returns:
            Formatted report string.
        """
        run = self.get_latest()
        if not run:
            return "No recovery runs found."
        if fmt == "json":
            return RecoveryReport.to_json(run)
        if fmt == "html":
            return RecoveryReport.to_html(run)
        return RecoveryReport.to_markdown(run)

    def cleanup(self) -> None:
        """Removes all in-memory state (useful for test isolation)."""
        with self._lock:
            self._history.clear()
            snap_dir = self._snapshots._snapshot_dir
            if os.path.exists(snap_dir):
                shutil.rmtree(snap_dir, ignore_errors=True)
                os.makedirs(snap_dir, exist_ok=True)
