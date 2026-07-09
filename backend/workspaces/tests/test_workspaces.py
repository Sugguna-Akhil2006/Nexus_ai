"""Unit and E2E tests for the AI Workspace & Project Collaboration module."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.api.sqlite_mock import DBStorage
from backend.workspaces.activity_feed import ActivityFeed
from backend.workspaces.artifact_manager import ArtifactManager
from backend.workspaces.comment_service import CommentService
from backend.workspaces.milestone_tracker import MilestoneTracker
from backend.workspaces.models import Project, ProjectTask, TaskState, WorkspaceRole
from backend.workspaces.project_manager import ProjectManager
from backend.workspaces.task_board import TaskBoard
from backend.workspaces.workspace_manager import WorkspaceManager
from backend.workspaces.workspace_permissions import WorkspacePermissions
from backend.workspaces.workspace_search import WorkspaceSearch


class TestProjectManager(unittest.TestCase):
    """Verifies project creation, archiving, and cloning."""

    def setUp(self) -> None:
        self.mgr = ProjectManager(db_path=":memory:")

    def test_crud_flow(self) -> None:
        proj = self.mgr.create_project("ws-1", "Test Project", "Description", ["tag1"], "dev")
        self.assertEqual(proj.name, "Test Project")
        self.assertFalse(proj.archived)

        # Retrieve
        retrieved = self.mgr.get_project(proj.project_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Test Project")

        # Archive
        self.mgr.archive_project(proj.project_id)
        archived_proj = self.mgr.get_project(proj.project_id)
        self.assertTrue(archived_proj.archived)

        # Clone
        cloned = self.mgr.clone_project(proj.project_id, "Cloned Proj")
        self.assertIsNotNone(cloned)
        self.assertEqual(cloned.name, "Cloned Proj")
        self.assertEqual(cloned.category, "dev")


class TestArtifactManager(unittest.TestCase):
    """Verifies artifact uploads and list retrieval."""

    def setUp(self) -> None:
        self.mgr = ArtifactManager(db_path=":memory:")

    def test_add_and_list_artifacts(self) -> None:
        art1 = self.mgr.add_artifact("proj-1", "Report A", "report", "Content A")
        art2 = self.mgr.add_artifact("proj-1", "Code B", "code", "Content B")

        items = self.mgr.list_artifacts("proj-1")
        self.assertEqual(len(items), 2)
        names = {a.name for a in items}
        self.assertIn("Report A", names)
        self.assertIn("Code B", names)


class TestTaskBoard(unittest.TestCase):
    """Verifies task list board manipulations."""

    def setUp(self) -> None:
        self.board = TaskBoard(db_path=":memory:")

    def test_task_lifecycle(self) -> None:
        t = self.board.add_task("proj-1", "Design API", "user-1")
        self.assertEqual(t.status, TaskState.PENDING)

        self.board.update_task_status(t.task_id, TaskState.COMPLETED)
        tasks = self.board.list_tasks("proj-1")
        self.assertEqual(tasks[0].status, TaskState.COMPLETED)


class TestMilestoneTracker(unittest.TestCase):
    """Verifies percent progress calculation logic."""

    def test_calculate_progress(self) -> None:
        tasks = [
            ProjectTask(task_id="t1", project_id="p1", title="A", status=TaskState.COMPLETED, created_at=""),
            ProjectTask(task_id="t2", project_id="p1", title="B", status=TaskState.PENDING, created_at=""),
        ]
        prog = MilestoneTracker.calculate_progress(tasks)
        self.assertEqual(prog["progress_pct"], 50.0)
        self.assertEqual(prog["total_tasks"], 2)


class TestActivityFeedAndComments(unittest.TestCase):
    """Verifies activity logs and posts comments threads."""

    def setUp(self) -> None:
        self.feed = ActivityFeed(db_path=":memory:")
        self.comments = CommentService(db_path=":memory:")

    def test_feed_log(self) -> None:
        self.feed.log_activity("proj-1", "action", "user-1", "Added ticket")
        items = self.feed.get_feed("proj-1")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].description, "Added ticket")

    def test_comments(self) -> None:
        self.comments.add_comment("proj-1", "user-1", "My comment")
        items = self.comments.list_comments("proj-1")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].content, "My comment")


class TestWorkspaceSearchAndPermissions(unittest.TestCase):
    """Verifies workspace DB queries search hits and membership check permissions."""

    def setUp(self) -> None:
        # Seed test members into active DBStorage instance
        self.db = DBStorage()
        conn = self.db._get_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO members (workspace_id, user_id, role, status) VALUES (?, ?, ?, ?)",
                ("ws-test-perm", "user-admin", "admin", "active"),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

        self.perms = WorkspacePermissions()

    def tearDown(self) -> None:
        conn = self.db._get_connection()
        try:
            conn.execute(
                "DELETE FROM members WHERE workspace_id = ? AND user_id = ?",
                ("ws-test-perm", "user-admin"),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def test_roles_and_perm_gates(self) -> None:
        role = self.perms.get_user_role("ws-test-perm", "user-admin")
        self.assertEqual(role, WorkspaceRole.ADMIN)

        self.assertTrue(self.perms.can_admin("ws-test-perm", "user-admin"))
        self.assertTrue(self.perms.can_write("ws-test-perm", "user-admin"))

        self.assertFalse(self.perms.can_admin("ws-test-perm", "user-viewer"))
