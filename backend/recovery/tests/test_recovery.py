"""Comprehensive tests for the Disaster Recovery & Business Continuity framework."""

from __future__ import annotations

import os
import shutil
import tempfile
import threading
import unittest

from backend.recovery.backup_scheduler import BackupScheduler
from backend.recovery.checkpoint_store import CheckpointStore
from backend.recovery.health_recovery import HealthRecovery
from backend.recovery.models import (
    BackupType,
    Checkpoint,
    CheckpointType,
    FailureScenario,
    RecoveryStatus,
    RestoreRequest,
)
from backend.recovery.provider_recovery import ProviderRecovery
from backend.recovery.recovery_manager import RecoveryManager
from backend.recovery.recovery_report import RecoveryReport
from backend.recovery.snapshot_manager import SnapshotManager
from backend.recovery.state_restorer import StateRestorer
from backend.recovery.workflow_recovery import WorkflowRecovery


# ======================================================================
# Fixtures
# ======================================================================

def _make_checkpoint(
    ctype: CheckpointType = CheckpointType.WORKFLOW,
    component_id: str = "wf-001",
    state: dict | None = None,
) -> Checkpoint:
    return Checkpoint(
        checkpoint_id=CheckpointStore.generate_id(),
        checkpoint_type=ctype,
        component_id=component_id,
        state=state or {"status": "running", "step": 3},
    )


# ======================================================================
# Checkpoint Store
# ======================================================================

class TestCheckpointStore(unittest.TestCase):
    """Verifies SQLite persistence for checkpoints."""

    def setUp(self) -> None:
        # Use a fresh in-memory store per test class
        self.store = CheckpointStore(db_path=":memory:")

    def test_save_and_get(self) -> None:
        cp = _make_checkpoint()
        self.store.save(cp)
        result = self.store.get(cp.checkpoint_id)
        self.assertIsNotNone(result)
        self.assertEqual(result.component_id, "wf-001")

    def test_list_by_component(self) -> None:
        for i in range(3):
            self.store.save(_make_checkpoint(component_id=f"comp-{i}"))
        self.store.save(_make_checkpoint(component_id="comp-0"))
        found = self.store.list_by_component("comp-0")
        self.assertEqual(len(found), 2)

    def test_list_by_type(self) -> None:
        self.store.save(_make_checkpoint(ctype=CheckpointType.SESSION, component_id="sess-1"))
        self.store.save(_make_checkpoint(ctype=CheckpointType.WORKFLOW, component_id="wf-1"))
        sessions = self.store.list_by_type(CheckpointType.SESSION)
        self.assertEqual(len(sessions), 1)

    def test_delete(self) -> None:
        cp = _make_checkpoint()
        self.store.save(cp)
        self.store.delete(cp.checkpoint_id)
        self.assertIsNone(self.store.get(cp.checkpoint_id))

    def test_thread_safe_concurrent_saves(self) -> None:
        # Use a fresh isolated store so prior test data doesn't skew the count
        import sqlite3, tempfile, os
        tmp = tempfile.mktemp(suffix=".db")
        isolated = CheckpointStore(db_path=tmp)
        errors: list[str] = []

        def save_one(i: int) -> None:
            try:
                isolated.save(_make_checkpoint(component_id=f"thread-{i}"))
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=save_one, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [], f"Concurrency errors: {errors}")
        all_checkpoints = isolated.list_all()
        self.assertEqual(len(all_checkpoints), 20)
        try:
            os.remove(tmp)
        except OSError:
            pass


# ======================================================================
# Snapshot Manager
# ======================================================================

class TestSnapshotManager(unittest.TestCase):
    """Verifies full, incremental, and metadata backup creation."""

    def setUp(self) -> None:
        self.store = CheckpointStore(db_path=":memory:")
        self.tmp_dir = tempfile.mkdtemp()
        self.manager = SnapshotManager(self.store, snapshot_dir=self.tmp_dir)
        # Seed checkpoints
        for ctype in (CheckpointType.WORKFLOW, CheckpointType.KNOWLEDGE, CheckpointType.SESSION):
            self.store.save(_make_checkpoint(ctype=ctype, component_id="comp-a"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_full_backup(self) -> None:
        record = self.manager.take_full_backup()
        self.assertEqual(record.backup_type, BackupType.FULL)
        self.assertGreater(record.size_bytes, 0)
        self.assertGreater(len(record.checkpoint_ids), 0)

    def test_incremental_backup(self) -> None:
        record = self.manager.take_incremental_backup()
        self.assertEqual(record.backup_type, BackupType.INCREMENTAL)

    def test_metadata_backup(self) -> None:
        record = self.manager.take_metadata_backup()
        self.assertEqual(record.backup_type, BackupType.METADATA)

    def test_list_backups(self) -> None:
        self.manager.take_full_backup()
        self.manager.take_metadata_backup()
        self.assertEqual(len(self.manager.list_backups()), 2)

    def test_archive_file_created(self) -> None:
        record = self.manager.take_full_backup()
        path = os.path.join(self.tmp_dir, f"{record.backup_id}.json")
        self.assertTrue(os.path.exists(path))


# ======================================================================
# State Restorer
# ======================================================================

class TestStateRestorer(unittest.TestCase):
    """Verifies single, component, and type restore strategies."""

    def setUp(self) -> None:
        self.store = CheckpointStore(db_path=":memory:")
        self.restorer = StateRestorer(self.store)
        self.cp = _make_checkpoint(component_id="svc-1")
        self.store.save(self.cp)

    def test_restore_by_checkpoint_id(self) -> None:
        req = RestoreRequest(checkpoint_id=self.cp.checkpoint_id)
        result = self.restorer.restore_from_request(req)
        self.assertTrue(result.success)
        self.assertIn(self.cp.checkpoint_id, result.restored_checkpoints)

    def test_restore_by_component(self) -> None:
        req = RestoreRequest(component_id="svc-1")
        result = self.restorer.restore_from_request(req)
        self.assertTrue(result.success)

    def test_restore_by_type(self) -> None:
        req = RestoreRequest(checkpoint_type=CheckpointType.WORKFLOW)
        result = self.restorer.restore_from_request(req)
        self.assertTrue(result.success)

    def test_restore_missing_id(self) -> None:
        req = RestoreRequest(checkpoint_id="does-not-exist")
        result = self.restorer.restore_from_request(req)
        self.assertFalse(result.success)

    def test_empty_request_fails(self) -> None:
        req = RestoreRequest()
        result = self.restorer.restore_from_request(req)
        self.assertFalse(result.success)


# ======================================================================
# Workflow Recovery
# ======================================================================

class TestWorkflowRecovery(unittest.TestCase):
    """Verifies interrupted workflow detection and resume."""

    def setUp(self) -> None:
        self.store = CheckpointStore(db_path=":memory:")
        self.handler = WorkflowRecovery(self.store)

    def test_no_interrupted_workflows(self) -> None:
        event = self.handler.recover()
        self.assertEqual(event.status, RecoveryStatus.COMPLETED)

    def test_resumes_interrupted_workflow(self) -> None:
        cp = _make_checkpoint(state={"status": "interrupted", "step": 2})
        self.store.save(cp)
        event = self.handler.recover()
        self.assertEqual(event.status, RecoveryStatus.COMPLETED)
        # State should now be "resumed"
        updated = self.store.get(cp.checkpoint_id)
        self.assertEqual(updated.state["status"], "resumed")


# ======================================================================
# Health Recovery
# ======================================================================

class TestHealthRecovery(unittest.TestCase):
    """Verifies subsystem health probes."""

    def test_recover_returns_event(self) -> None:
        event = HealthRecovery().recover()
        self.assertIn(event.status, list(RecoveryStatus))
        self.assertIn("subsystem", event.detail)


# ======================================================================
# Provider Recovery
# ======================================================================

class TestProviderRecovery(unittest.TestCase):
    """Verifies provider recovery handler."""

    def test_recover_returns_event(self) -> None:
        event = ProviderRecovery().recover()
        self.assertIn(event.status, list(RecoveryStatus))
        self.assertEqual(event.component, "provider_registry")


# ======================================================================
# Backup Scheduler
# ======================================================================

class TestBackupScheduler(unittest.TestCase):
    """Verifies scheduler fires callbacks at the right interval."""

    def test_scheduler_fires(self) -> None:
        fired: list[BackupType] = []

        def callback(btype: BackupType) -> object:
            fired.append(btype)
            return object()

        sched = BackupScheduler(callback=callback)
        sched.add_job("test_job", BackupType.FULL, interval_seconds=0.05)
        sched.start()
        import time
        time.sleep(0.2)  # Allow ≥ 3 firings
        sched.stop()
        self.assertGreater(len(fired), 0)


# ======================================================================
# Recovery Manager E2E
# ======================================================================

class TestRecoveryManagerE2E(unittest.TestCase):
    """End-to-end tests covering checkpoint→backup→restore→recover cycle."""

    def setUp(self) -> None:
        self.manager = RecoveryManager()
        self.manager.cleanup()

    def test_checkpoint_and_list(self) -> None:
        self.manager.save_checkpoint(
            CheckpointType.WORKFLOW, "wf-e2e", {"status": "running"}
        )
        cps = self.manager.list_checkpoints("wf-e2e")
        self.assertEqual(len(cps), 1)

    def test_backup_and_list(self) -> None:
        self.manager.save_checkpoint(CheckpointType.SESSION, "sess-1", {"user": "alice"})
        record = self.manager.backup(BackupType.FULL)
        self.assertEqual(record.backup_type, BackupType.FULL)
        self.assertEqual(len(self.manager.list_backups()), 1)

    def test_recover_application_restart(self) -> None:
        run = self.manager.recover(FailureScenario.APPLICATION_RESTART)
        self.assertIn(run.status, list(RecoveryStatus))
        self.assertGreater(len(run.timeline), 0)
        self.assertGreater(run.duration_ms, 0)

    def test_recover_workflow_failure(self) -> None:
        # Seed an interrupted workflow checkpoint
        self.manager.save_checkpoint(
            CheckpointType.WORKFLOW, "wf-crash", {"status": "interrupted"}
        )
        run = self.manager.recover(FailureScenario.PARTIAL_WORKFLOW_FAILURE)
        self.assertIn(run.status, list(RecoveryStatus))

    def test_history_tracked(self) -> None:
        self.manager.recover(FailureScenario.APPLICATION_RESTART)
        self.manager.recover(FailureScenario.WORKER_CRASH)
        self.assertEqual(len(self.manager.get_history()), 2)


# ======================================================================
# Report Generator
# ======================================================================

class TestRecoveryReport(unittest.TestCase):
    """Verifies report output formats."""

    def setUp(self) -> None:
        self.manager = RecoveryManager()
        self.manager.cleanup()
        self.run = self.manager.recover(FailureScenario.APPLICATION_RESTART)

    def test_markdown_contains_run_id(self) -> None:
        md = RecoveryReport.to_markdown(self.run)
        self.assertIn(self.run.run_id, md)
        self.assertIn("Recovery Timeline", md)

    def test_json_parseable(self) -> None:
        import json
        raw = RecoveryReport.to_json(self.run)
        data = json.loads(raw)
        self.assertIn("run_id", data)

    def test_html_structure(self) -> None:
        html = RecoveryReport.to_html(self.run)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn(self.run.run_id, html)
