"""Central migration manager coordinating schema, config, plugin, and workflow upgrades."""

from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.migration.breaking_change_detector import BreakingChangeDetector
from backend.migration.compatibility_checker import CompatibilityChecker
from backend.migration.config_migrator import ConfigMigrator
from backend.migration.models import (
    CompatibilityReport,
    MigrationKind,
    MigrationPlan,
    MigrationRun,
    MigrationStatus,
    MigrationStep,
)
from backend.migration.plugin_migrator import PluginMigrator
from backend.migration.rollback_manager import RollbackManager
from backend.migration.schema_migrator import SchemaMigrator
from backend.migration.workflow_migrator import WorkflowMigrator


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class MigrationManager:
    """Thread-safe singleton orchestrating the whole upgrade and compatibility lifecycle."""

    _instance: Optional["MigrationManager"] = None

    def __new__(cls) -> "MigrationManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_ready", False):
            return
        self._lock = threading.RLock()
        self._schema_migrator = SchemaMigrator(db_path=":memory:")
        self._rollback_manager = RollbackManager(db_path=":memory:")
        self._history: List[MigrationRun] = []
        self._ready = True

    # ------------------------------------------------------------------
    # Compatibility & Checking
    # ------------------------------------------------------------------

    def check_compatibility(self, from_version: str, to_version: str) -> CompatibilityReport:
        """Runs the compatibility suite and flags any breaking API/manifest surfaces."""
        report = CompatibilityChecker.check(from_version, to_version)
        report.breaking_changes = BreakingChangeDetector.detect(from_version, to_version)
        return report

    # ------------------------------------------------------------------
    # Migration execution
    # ------------------------------------------------------------------

    def plan(self, from_version: str, to_version: str) -> MigrationPlan:
        """Prepares an ordered plan containing schema and config upgrade steps."""
        steps: List[MigrationStep] = []
        steps.extend(self._schema_migrator.get_steps(from_version, to_version))
        steps.extend(ConfigMigrator.get_steps(from_version, to_version))
        steps.extend(PluginMigrator.get_steps(from_version, to_version))
        steps.extend(WorkflowMigrator.get_steps(from_version, to_version))

        return MigrationPlan(
            plan_id=str(uuid.uuid4())[:8],
            from_version=from_version,
            to_version=to_version,
            steps=steps,
        )

    def run(
        self,
        from_version: str,
        to_version: str,
        config: Dict[str, Any],
        plugins: Optional[List[dict]] = None,
        workflows: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[MigrationRun, Dict[str, Any]]:
        """Executes the full migration suite with automatic rollback on step failure.

        Returns:
            Tuple of (completed/failed MigrationRun, migrated config dictionary).
        """
        with self._lock:
            plan = self.plan(from_version, to_version)
            run_id = str(uuid.uuid4())[:8]
            t_start = time.perf_counter()

            run = MigrationRun(
                run_id=run_id,
                plan_id=plan.plan_id,
                from_version=from_version,
                to_version=to_version,
                status=MigrationStatus.RUNNING,
                steps=plan.steps,
            )

            # Apply DDL schema steps
            schema_steps = [s for s in run.steps if s.kind == MigrationKind.SCHEMA]
            if schema_steps:
                applied = self._schema_migrator.apply(from_version, to_version)
                for orig, app in zip(schema_steps, applied):
                    orig.status = app.status
                    orig.error = app.error
                    orig.applied_at = app.applied_at
                    orig.duration_ms = app.duration_ms

            # Config steps
            cfg_steps = [s for s in run.steps if s.kind == MigrationKind.CONFIG]
            migrated_config = config.copy()
            if cfg_steps:
                migrated_config, applied_cfg = ConfigMigrator.apply(config, from_version, to_version)
                for orig, app in zip(cfg_steps, applied_cfg):
                    orig.status = app.status
                    orig.error = app.error
                    orig.applied_at = app.applied_at
                    orig.duration_ms = app.duration_ms

            # Plugin steps
            plug_steps = [s for s in run.steps if s.kind == MigrationKind.PLUGIN]
            if plug_steps:
                _, applied_plug = PluginMigrator.apply(plugins or [], from_version, to_version)
                for orig, app in zip(plug_steps, applied_plug):
                    orig.status = app.status
                    orig.error = app.error
                    orig.applied_at = app.applied_at
                    orig.duration_ms = app.duration_ms

            # Workflow steps
            wf_steps = [s for s in run.steps if s.kind == MigrationKind.WORKFLOW]
            if wf_steps:
                _, applied_wf = WorkflowMigrator.apply(workflows or [], from_version, to_version)
                for orig, app in zip(wf_steps, applied_wf):
                    orig.status = app.status
                    orig.error = app.error
                    orig.applied_at = app.applied_at
                    orig.duration_ms = app.duration_ms

            # Assess failure & rollback
            run.errors = [s.error for s in run.steps if s.status == MigrationStatus.FAILED and s.error]
            if run.errors:
                run.status = MigrationStatus.FAILED
                # Revert all successfully applied steps
                self._rollback_manager.rollback(run_id, run.steps, config)
            else:
                run.status = MigrationStatus.COMPLETED

            run.completed_at = _utcnow()
            run.duration_ms = round((time.perf_counter() - t_start) * 1000, 2)

            self._history.append(run)
            return run, migrated_config

    # ------------------------------------------------------------------
    # History & reporting
    # ------------------------------------------------------------------

    def get_history(self) -> List[MigrationRun]:
        """Returns all past migration run records."""
        with self._lock:
            return list(self._history)

    def get_latest(self) -> Optional[MigrationRun]:
        """Returns the most recent migration run."""
        with self._lock:
            return self._history[-1] if self._history else None

    def cleanup(self) -> None:
        """Wipes run logs for test isolation."""
        with self._lock:
            self._history.clear()
            self._schema_migrator = SchemaMigrator(db_path=":memory:")
            self._rollback_manager = RollbackManager(db_path=":memory:")
