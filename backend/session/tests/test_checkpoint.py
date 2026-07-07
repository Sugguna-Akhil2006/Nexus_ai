"""Tests for session checkpoints and rollbacks."""

import unittest
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.project_context import ProjectContext
from backend.session.reasoning_history import ReasoningHistory
from backend.session.checkpoint_manager import CheckpointManager
from backend.session.models import CheckpointType, DecisionType


class TestCheckpoint(unittest.TestCase):
    """Verifies that CheckpointManager captures and restores system states."""

    def test_checkpoint_lifecycle(self) -> None:
        """Tests taking a checkpoint, modifying state, and restoring back."""
        ws_mem = WorkspaceMemory()
        proj_ctx = ProjectContext()
        reasoning = ReasoningHistory()
        mgr = CheckpointManager(ws_mem, proj_ctx, reasoning)

        # 1. Establish initial state
        ws_mem.update_project("Project Alpha")
        ws_mem.add_pending_task("Task 1")
        proj_ctx.add_goal("Goal 1")
        proj_ctx.record_decision("Dec 1", "Initial design", DecisionType.ARCHITECTURE)
        reasoning.record_question("Q1")

        # 2. Take checkpoint
        cp = mgr.create_checkpoint(
            checkpoint_type=CheckpointType.MANUAL_SAVE,
            description="Initial Save"
        )
        self.assertEqual(len(mgr.get_checkpoints()), 1)

        # 3. Alter states
        ws_mem.update_project("Project Beta")
        ws_mem.add_pending_task("Task 2")
        proj_ctx.add_goal("Goal 2")
        reasoning.record_question("Q2")

        self.assertEqual(ws_mem.get_snapshot().current_project, "Project Beta")

        # 4. Restore checkpoint and assert rollback
        mgr.restore_checkpoint(cp.checkpoint_id)

        self.assertEqual(ws_mem.get_snapshot().current_project, "Project Alpha")
        self.assertEqual(ws_mem.get_snapshot().pending_tasks, ["Task 1"])
        self.assertEqual(proj_ctx.get_snapshot().goals, ["Goal 1"])
        self.assertEqual(reasoning.get_snapshot().questions_asked, ["Q1"])
