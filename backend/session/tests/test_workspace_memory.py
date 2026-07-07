"""Tests for workspace memory state tracking and thread-safety."""

import threading
import unittest
from backend.session.workspace_memory import WorkspaceMemory
from backend.session.models import WorkspaceMemoryModel


class TestWorkspaceMemory(unittest.TestCase):
    """Verifies that WorkspaceMemory works correctly and is thread-safe."""

    def test_basic_crud(self) -> None:
        """Tests standard updates and list additions."""
        memory = WorkspaceMemory()
        memory.update_project("Nexus")
        memory.set_objective("Build Session Intelligence")
        memory.add_recent_file("session_manager.py")
        memory.add_recent_file("models.py")
        # Ensure ordering (most recent first)
        memory.add_recent_file("session_manager.py")
        memory.add_pending_task("Implement Tests")
        memory.add_recent_workflow("wf-1")
        memory.add_recent_analysis("an-1")

        snapshot = memory.get_snapshot()
        self.assertEqual(snapshot.current_project, "Nexus")
        self.assertEqual(snapshot.current_objective, "Build Session Intelligence")
        self.assertEqual(snapshot.recent_files, ["session_manager.py", "models.py"])
        self.assertEqual(snapshot.recent_workflows, ["wf-1"])
        self.assertEqual(snapshot.recent_analyses, ["an-1"])
        self.assertEqual(snapshot.pending_tasks, ["Implement Tests"])

    def test_load_snapshot(self) -> None:
        """Tests restoring workspace state from a snapshot model."""
        memory = WorkspaceMemory()
        model = WorkspaceMemoryModel(
            current_project="Nexus Core",
            recent_files=["test.py"],
            current_objective="Fix Lints",
            pending_tasks=["Clean code"]
        )
        memory.load_snapshot(model)
        snapshot = memory.get_snapshot()
        self.assertEqual(snapshot.current_project, "Nexus Core")
        self.assertEqual(snapshot.recent_files, ["test.py"])

    def test_thread_safety(self) -> None:
        """Concurrently updates workspace memory to verify thread safety."""
        memory = WorkspaceMemory()

        def worker(index: int) -> None:
            for i in range(50):
                memory.add_recent_file(f"file_{index}_{i}.py")
                memory.add_pending_task(f"task_{index}_{i}")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        snapshot = memory.get_snapshot()
        self.assertEqual(len(snapshot.recent_files), 500)
        self.assertEqual(len(snapshot.pending_tasks), 500)
