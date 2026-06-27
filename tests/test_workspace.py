import concurrent.futures
from datetime import datetime, timedelta
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from core.workspace import (
    WorkspaceError,
    WorkspaceValidationError,
    WorkspaceNotFoundError,
    WorkspaceRole,
    Workspace,
    WorkspaceMember,
    Project,
    KnowledgeSpace,
    ConversationReference,
    WorkspaceProvider,
    WorkspaceRegistry,
    WorkspaceContextResolver,
    WorkspaceAgent,
    validate_workspace_name,
    validate_workspace_id,
    validate_member_role,
    validate_indexing_status,
)
from core.base import AgentState, AgentStatus
from core.event import Event, EventBus, EventType
from core.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class InMemoryWorkspaceProvider(WorkspaceProvider):
    """In-memory persistence implementation for WorkspaceProvider interface testing."""

    def __init__(self) -> None:
        self.workspaces: Dict[str, Workspace] = {}
        self.members: Dict[str, List[WorkspaceMember]] = {}
        self.projects: Dict[str, List[Project]] = {}
        self.knowledge_spaces: Dict[str, List[KnowledgeSpace]] = {}
        self.conversations: Dict[str, List[ConversationReference]] = {}
        self.health_healthy = True

    def create_workspace(self, workspace: Workspace) -> Workspace:
        self.workspaces[workspace.workspace_id] = workspace
        self.members[workspace.workspace_id] = []
        self.projects[workspace.workspace_id] = []
        self.knowledge_spaces[workspace.workspace_id] = []
        self.conversations[workspace.workspace_id] = []
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        return self.workspaces.get(workspace_id)

    def update_workspace(self, workspace: Workspace) -> Workspace:
        self.workspaces[workspace.workspace_id] = workspace
        return workspace

    def delete_workspace(self, workspace_id: str) -> bool:
        if workspace_id in self.workspaces:
            del self.workspaces[workspace_id]
            self.members.pop(workspace_id, None)
            self.projects.pop(workspace_id, None)
            self.knowledge_spaces.pop(workspace_id, None)
            self.conversations.pop(workspace_id, None)
            return True
        return False

    def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        ws_id = member.workspace_id
        if ws_id not in self.members:
            self.members[ws_id] = []
        self.members[ws_id].append(member)
        return member

    def get_members(self, workspace_id: str) -> List[WorkspaceMember]:
        return self.members.get(workspace_id, [])

    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        if workspace_id in self.members:
            original_len = len(self.members[workspace_id])
            self.members[workspace_id] = [m for m in self.members[workspace_id] if m.user_id != user_id]
            return len(self.members[workspace_id]) < original_len
        return False

    def create_project(self, project: Project) -> Project:
        ws_id = project.workspace_id
        if ws_id not in self.projects:
            self.projects[ws_id] = []
        self.projects[ws_id].append(project)
        return project

    def list_projects(self, workspace_id: str) -> List[Project]:
        return self.projects.get(workspace_id, [])

    def create_knowledge_space(self, space: KnowledgeSpace) -> KnowledgeSpace:
        ws_id = space.workspace_id
        if ws_id not in self.knowledge_spaces:
            self.knowledge_spaces[ws_id] = []
        self.knowledge_spaces[ws_id].append(space)
        return space

    def get_knowledge_spaces(self, workspace_id: str) -> List[KnowledgeSpace]:
        return self.knowledge_spaces.get(workspace_id, [])

    def create_conversation_reference(self, ref: ConversationReference) -> ConversationReference:
        ws_id = ref.workspace_id
        if ws_id not in self.conversations:
            self.conversations[ws_id] = []
        self.conversations[ws_id].append(ref)
        return ref

    def get_conversations(self, workspace_id: str) -> List[ConversationReference]:
        return self.conversations.get(workspace_id, [])

    def health_check(self) -> bool:
        return self.health_healthy


class TestWorkspaceSystem(unittest.TestCase):
    """Suite of tests covering Workspace management system."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = WorkspaceRegistry()
        with self.registry._lock:
            self.registry._providers.clear()

        self.provider = InMemoryWorkspaceProvider()
        self.registry.register_provider("memory", self.provider)

        self.agent = WorkspaceAgent()
        self.agent.initialize()

    def test_validation_utilities(self) -> None:
        """Verifies syntax validations for workspace properties."""
        validate_workspace_name("My Workspace")
        validate_workspace_id("ws-123")
        validate_member_role("owner")
        validate_member_role("VIEWER")
        validate_indexing_status("indexed")
        validate_indexing_status("INDEXING")

        with self.assertRaises(WorkspaceValidationError):
            validate_workspace_name("ab")
        with self.assertRaises(WorkspaceValidationError):
            validate_workspace_id("")
        with self.assertRaises(WorkspaceValidationError):
            validate_member_role("invalid-role")
        with self.assertRaises(WorkspaceValidationError):
            validate_indexing_status("unknown")

    def test_model_immutability(self) -> None:
        """Verifies workspace properties enforce dataclass freezing."""
        ws = Workspace(
            workspace_id="1", name="n", description="d", owner_id="u",
            organization_id="o", created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(), status="active"
        )
        with self.assertRaises(AttributeError):
            ws.name = "new name"  # type: ignore

    def test_registry_singleton(self) -> None:
        """Verifies singleton behavior of WorkspaceRegistry."""
        registry2 = WorkspaceRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration(self) -> None:
        """Verifies registrations validations on WorkspaceRegistry."""
        with self.assertRaises(WorkspaceValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(WorkspaceValidationError):
            self.registry.register_provider("memory2", None)  # type: ignore
        with self.assertRaises(WorkspaceValidationError):
            self.registry.register_provider("memory", self.provider)

        self.registry.unregister_provider("memory")
        self.assertNotIn("memory", self.registry.list_providers())

    def test_registry_health_checks(self) -> None:
        """Verifies health monitoring propagation."""
        health = self.registry.health_check()
        self.assertTrue(health["memory"])

        self.provider.health_healthy = False
        health = self.registry.health_check()
        self.assertFalse(health["memory"])

    def test_context_resolver(self) -> None:
        """Verifies context resolution role permission derivations."""
        resolver = WorkspaceContextResolver(self.provider)

        # 1. Create Workspace
        now = datetime.utcnow()
        ws = Workspace(
            workspace_id="ws_1",
            name="Workspace 1",
            description="",
            owner_id="user_owner",
            organization_id="org_1",
            created_at=now,
            updated_at=now,
            status="active"
        )
        self.provider.create_workspace(ws)

        # 2. Add projects & space
        p = Project("proj_1", "ws_1", "Project 1", "", now)
        self.provider.create_project(p)

        ks = KnowledgeSpace("space_1", "ws_1", "Base", "", "indexed")
        self.provider.create_knowledge_space(ks)

        # 3. Add active member
        m = WorkspaceMember("mem_1", "ws_1", "user_editor", "EDITOR", now, "active")
        self.provider.add_member(m)

        # 4. Resolve Context for Editor
        ctx = resolver.resolve_context(
            user_id="user_editor",
            workspace_id="ws_1",
            project_id="proj_1",
            knowledge_space_id="space_1"
        )
        self.assertEqual(ctx.workspace.name, "Workspace 1")
        self.assertEqual(ctx.project.name, "Project 1")
        self.assertEqual(ctx.knowledge_space.name, "Base")
        self.assertEqual(ctx.member_role, WorkspaceRole.EDITOR)
        self.assertIn("WRITE", ctx.permissions)

        # 5. Non-members should be blocked
        with self.assertRaises(WorkspaceValidationError):
            resolver.resolve_context("user_intruder", "ws_1")

        # 6. Mismatched resources should be rejected
        with self.assertRaises(WorkspaceValidationError):
            resolver.resolve_context("user_editor", "ws_1", project_id="proj_mismatched")

        # 7. Owner bypass validation checks
        ctx_owner = resolver.resolve_context("user_owner", "ws_1")
        self.assertEqual(ctx_owner.member_role, WorkspaceRole.OWNER)

    def test_archived_workspace_access(self) -> None:
        """Verifies archived workspace access parameters."""
        resolver = WorkspaceContextResolver(self.provider)
        now = datetime.utcnow()
        ws = Workspace(
            workspace_id="ws_1", name="W", description="", owner_id="user_owner",
            organization_id="org_1", created_at=now, updated_at=now, status="archived"
        )
        self.provider.create_workspace(ws)
        self.provider.add_member(WorkspaceMember("m", "ws_1", "user_viewer", "VIEWER", now, "active"))

        # Owner has access
        ctx_owner = resolver.resolve_context("user_owner", "ws_1")
        self.assertEqual(ctx_owner.workspace.status, "archived")

        # Non-owners are blocked from archived
        with self.assertRaises(WorkspaceValidationError):
            resolver.resolve_context("user_viewer", "ws_1")

    def test_agent_create_and_update_workspace(self) -> None:
        """Verifies WorkspaceAgent task executing for workspace creation and updates."""
        task_create = Task(
            description="Create workspace profile",
            metadata={
                "action": "create_workspace",
                "workspace_id": "ws_agent_1",
                "name": "Agent Workspace",
                "owner_id": "user_owner"
            }
        )
        self.agent.validate_task(task_create)
        self.agent.before_execute(task_create)
        ws = self.agent.execute(task_create)
        self.agent.after_execute(ws)

        self.assertEqual(ws.name, "Agent Workspace")
        self.assertEqual(ws.owner_id, "user_owner")

        # Verify event was published
        self.event_bus.dispatch_all()
        events = [e for e in self.receiver.events if e.payload.get("event_name") == "workspace.created"]
        self.assertEqual(len(events), 1)

        # Update
        task_update = Task(
            description="Update workspace description",
            metadata={
                "action": "update_workspace",
                "workspace_id": "ws_agent_1",
                "description": "New updated description"
            }
        )
        self.agent.validate_task(task_update)
        self.agent.before_execute(task_update)
        updated_ws = self.agent.execute(task_update)
        self.agent.after_execute(updated_ws)

        self.assertEqual(updated_ws.description, "New updated description")

    def test_agent_membership_tasks(self) -> None:
        """Verifies member adding and removal agent tasks."""
        # 1. Create Workspace first
        task_create = Task(
            description="Create WS",
            metadata={
                "action": "create_workspace",
                "workspace_id": "ws_1",
                "name": "Workspace WS",
                "owner_id": "user_owner"
            }
        )
        self.agent.validate_task(task_create)
        self.agent.before_execute(task_create)
        self.agent.execute(task_create)
        self.agent.after_execute(None)

        # 2. Add Member Task
        task_add = Task(
            description="Add member",
            metadata={
                "action": "add_member",
                "workspace_id": "ws_1",
                "user_id": "user_member",
                "role": "MEMBER"
            }
        )
        self.agent.validate_task(task_add)
        self.agent.before_execute(task_add)
        m = self.agent.execute(task_add)
        self.agent.after_execute(m)

        self.assertEqual(m.role, "MEMBER")

        # Verify event
        self.event_bus.dispatch_all()
        events = [e for e in self.receiver.events if e.payload.get("event_name") == "workspace.member.added"]
        self.assertEqual(len(events), 1)

        # 3. Remove Member Task
        task_rem = Task(
            description="Remove member",
            metadata={
                "action": "remove_member",
                "workspace_id": "ws_1",
                "user_id": "user_member"
            }
        )
        self.agent.validate_task(task_rem)
        self.agent.before_execute(task_rem)
        success = self.agent.execute(task_rem)
        self.agent.after_execute(success)

        self.assertTrue(success)

    def test_agent_project_and_context_tasks(self) -> None:
        """Verifies project creation and context resolution tasks."""
        # Setup WS
        task_create = Task(
            description="Create WS",
            metadata={
                "action": "create_workspace",
                "workspace_id": "ws_1",
                "name": "Workspace WS",
                "owner_id": "user_owner"
            }
        )
        self.agent.validate_task(task_create)
        self.agent.before_execute(task_create)
        self.agent.execute(task_create)
        self.agent.after_execute(None)

        # Create Project
        task_proj = Task(
            description="Create project reference",
            metadata={
                "action": "create_project",
                "workspace_id": "ws_1",
                "project_id": "p_1",
                "name": "Project Alpha"
            }
        )
        self.agent.validate_task(task_proj)
        self.agent.before_execute(task_proj)
        p = self.agent.execute(task_proj)
        self.agent.after_execute(p)

        self.assertEqual(p.name, "Project Alpha")

        # Resolve Context Task
        task_resolve = Task(
            description="Resolve active context",
            metadata={
                "action": "resolve_context",
                "workspace_id": "ws_1",
                "user_id": "user_owner",
                "project_id": "p_1"
            }
        )
        self.agent.validate_task(task_resolve)
        self.agent.before_execute(task_resolve)
        ctx = self.agent.execute(task_resolve)
        self.agent.after_execute(ctx)

        self.assertEqual(ctx.workspace.workspace_id, "ws_1")
        self.assertEqual(ctx.project.project_id, "p_1")

    def test_thread_safety_registry(self) -> None:
        """Verifies concurrent registrations operate safely."""
        def run_thread(tid: int) -> None:
            class DummyWSProvider(WorkspaceProvider):
                def create_workspace(self, workspace): return workspace
                def get_workspace(self, workspace_id): return None
                def update_workspace(self, workspace): return workspace
                def delete_workspace(self, workspace_id): return True
                def add_member(self, member): return member
                def get_members(self, workspace_id): return []
                def remove_member(self, workspace_id, user_id): return True
                def create_project(self, project): return project
                def list_projects(self, workspace_id): return []
                def create_knowledge_space(self, space): return space
                def get_knowledge_spaces(self, workspace_id): return []
                def create_conversation_reference(self, ref): return ref
                def get_conversations(self, workspace_id): return []
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummyWSProvider())
            self.assertIn(pid, self.registry.list_providers())
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
