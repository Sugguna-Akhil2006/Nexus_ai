"""Tests for concurrent session operations and isolation."""

import concurrent.futures
import unittest
from backend.session.session_manager import SessionManager


class TestConcurrentSessions(unittest.TestCase):
    """Verifies that multiple sessions can be accessed, updated, and queried concurrently."""

    def test_concurrent_creation_and_update(self) -> None:
        """Runs concurrent creation and updates to verify thread safety."""
        manager = SessionManager()

        def run_session_flow(index: int) -> str:
            # Create session
            inst = manager.create_session(f"Concurrent Session {index}")
            session_id = inst.model.session_id

            # Perform various updates
            manager.update_workspace_status(
                session_id=session_id,
                current_project=f"Project {index}",
                objective=f"Objective {index}",
                add_file=f"file_{index}.py",
                add_task=f"task_{index}"
            )

            # Record reasoning step
            inst.reasoning_history.record_step(f"Step {index}", confidence=0.8)

            # Return session id
            return session_id

        # Use ThreadPoolExecutor to run tasks concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_session_flow, i) for i in range(20)]
            session_ids = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(session_ids), 20)

        # Verify state integrity (no cross-contamination)
        for i, s_id in enumerate(session_ids):
            # Since threads complete in arbitrary order, we can map back using project title or name
            inst = manager.get_session(s_id)
            proj_name = inst.workspace_memory.get_snapshot().current_project
            # Parse index from project name
            idx = int(proj_name.split(" ")[1])

            self.assertEqual(inst.model.name, f"Concurrent Session {idx}")
            self.assertEqual(proj_name, f"Project {idx}")
            self.assertEqual(inst.workspace_memory.get_snapshot().current_objective, f"Objective {idx}")
            self.assertEqual(inst.workspace_memory.get_snapshot().recent_files, [f"file_{idx}.py"])
            self.assertEqual(len(inst.reasoning_history.get_snapshot().reasoning_steps), 1)
            self.assertEqual(inst.reasoning_history.get_snapshot().reasoning_steps[0].description, f"Step {idx}")
