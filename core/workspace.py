"""Workspace Agent and Multi-Tenant Resource Management Module.

Provides abstractions, registries, providers, and resolvers for workspaces,
projects, members, knowledge spaces, and workspace context validation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import threading
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from core.base import AgentState, AgentStatus, BaseAgent
from core.event import Event, EventBus, EventType
from core.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from core.task import Task
from core.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class WorkspaceError(NexusException):
    """Base exception for all Workspace Agent related errors."""
    pass


class WorkspaceValidationError(WorkspaceError):
    """Raised when workspace request parameters or inputs are invalid."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace or associated resource is not found."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class WorkspaceRole(Enum):
    """Predefined access roles within a workspace."""
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


@dataclass(frozen=True)
class Workspace:
    """Immutable model representing a multi-tenant workspace.

    Attributes:
        workspace_id: Unique string identifier.
        name: Name of the workspace.
        description: Description of the workspace.
        owner_id: User ID of the workspace creator/owner.
        organization_id: Organization context identifier.
        created_at: Creation timestamp.
        updated_at: Last modification timestamp.
        status: Current status (e.g. "active", "archived", "deleted").
        metadata: Custom metadata dictionary.
    """
    workspace_id: str
    name: str
    description: str
    owner_id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkspaceMember:
    """Represents a user associated with a workspace.

    Attributes:
        member_id: Unique member mapping ID.
        workspace_id: Workspace identifier.
        user_id: Associated user ID.
        role: Access role within the workspace.
        joined_at: Datetime indicating when membership started.
        status: Member status (e.g. "active", "invited", "suspended").
        metadata: Custom metadata dictionary.
    """
    member_id: str
    workspace_id: str
    user_id: str
    role: str
    joined_at: datetime
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Project:
    """Represents a specific project directory inside a workspace.

    Attributes:
        project_id: Unique project identifier.
        workspace_id: Workspace identifier.
        name: Name of the project.
        description: Description of the project.
        created_at: Creation timestamp.
        metadata: Custom metadata.
    """
    project_id: str
    workspace_id: str
    name: str
    description: str
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeSpace:
    """Represents a logical knowledge base namespace inside a workspace.

    Attributes:
        knowledge_space_id: Unique knowledge base namespace identifier.
        workspace_id: Workspace identifier.
        name: Name of the knowledge space.
        description: Description of the knowledge space.
        indexing_status: Indexing health status (e.g. "indexed", "indexing", "failed").
        metadata: Custom metadata.
    """
    knowledge_space_id: str
    workspace_id: str
    name: str
    description: str
    indexing_status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversationReference:
    """Represents metadata linking a conversation log to a workspace.

    Attributes:
        conversation_id: Unique conversation identifier.
        workspace_id: Workspace identifier.
        title: User-facing title.
        created_at: Creation timestamp.
        last_activity: Last activity update timestamp.
        metadata: Custom metadata.
    """
    conversation_id: str
    workspace_id: str
    title: str
    created_at: datetime
    last_activity: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_workspace_name(name: str) -> None:
    """Validates workspace name format.

    Args:
        name: Workspace name.

    Raises:
        WorkspaceValidationError: If validation fails.
    """
    if not name or not isinstance(name, str) or len(name.strip()) < 3:
        raise WorkspaceValidationError("Workspace name must be a non-empty string of at least 3 characters.")


def validate_workspace_id(workspace_id: str) -> None:
    """Validates workspace ID formatting.

    Args:
        workspace_id: Workspace ID.

    Raises:
        WorkspaceValidationError: If validation fails.
    """
    if not workspace_id or not isinstance(workspace_id, str) or not workspace_id.strip():
        raise WorkspaceValidationError("Workspace ID cannot be empty.")


def validate_member_role(role: str) -> None:
    """Validates workspace membership roles.

    Args:
        role: The role name.

    Raises:
        WorkspaceValidationError: If role is unrecognized.
    """
    valid_roles = {r.value for r in WorkspaceRole}
    if not role or str(role).upper() not in valid_roles:
        raise WorkspaceValidationError(f"Invalid workspace role: {role}")


def validate_indexing_status(status: str) -> None:
    """Validates knowledge space indexing statuses.

    Args:
        status: The indexing status.

    Raises:
        WorkspaceValidationError: If status is unrecognized.
    """
    valid_statuses = {"indexed", "indexing", "failed", "pending"}
    if not status or str(status).lower() not in valid_statuses:
        raise WorkspaceValidationError(f"Invalid indexing status: {status}")


# =====================================================================
# Provider Interface
# =====================================================================

class WorkspaceProvider(ABC):
    """Abstract contract for workspace storage/persistence systems."""

    @abstractmethod
    def create_workspace(self, workspace: Workspace) -> Workspace:
        """Saves a new Workspace profile.

        Args:
            workspace: The Workspace object.

        Returns:
            Workspace: Saved Workspace.
        """
        pass

    @abstractmethod
    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Retrieves Workspace profile.

        Args:
            workspace_id: Workspace ID.

        Returns:
            Optional[Workspace]: Found workspace, or None.
        """
        pass

    @abstractmethod
    def update_workspace(self, workspace: Workspace) -> Workspace:
        """Updates Workspace details.

        Args:
            workspace: Updated Workspace object.

        Returns:
            Workspace: Updated Workspace profile.
        """
        pass

    @abstractmethod
    def delete_workspace(self, workspace_id: str) -> bool:
        """Deletes/Removes a Workspace completely.

        Args:
            workspace_id: Workspace ID.

        Returns:
            bool: True if removed successfully.
        """
        pass

    @abstractmethod
    def add_member(self, member: WorkspaceMember) -> WorkspaceMember:
        """Adds a member mapping configuration.

        Args:
            member: WorkspaceMember object.

        Returns:
            WorkspaceMember: Saved membership.
        """
        pass

    @abstractmethod
    def get_members(self, workspace_id: str) -> List[WorkspaceMember]:
        """Retrieves membership list of a workspace.

        Args:
            workspace_id: Workspace ID.

        Returns:
            List[WorkspaceMember]: Workspace members list.
        """
        pass

    @abstractmethod
    def remove_member(self, workspace_id: str, user_id: str) -> bool:
        """Removes a member from workspace.

        Args:
            workspace_id: Workspace ID.
            user_id: Target user ID.

        Returns:
            bool: True if removed.
        """
        pass

    @abstractmethod
    def create_project(self, project: Project) -> Project:
        """Saves project reference.

        Args:
            project: The Project object.

        Returns:
            Project: Saved project.
        """
        pass

    @abstractmethod
    def list_projects(self, workspace_id: str) -> List[Project]:
        """Lists projects inside target workspace.

        Args:
            workspace_id: Workspace ID.

        Returns:
            List[Project]: Projects list.
        """
        pass

    @abstractmethod
    def create_knowledge_space(self, space: KnowledgeSpace) -> KnowledgeSpace:
        """Saves a knowledge space reference."""
        pass

    @abstractmethod
    def get_knowledge_spaces(self, workspace_id: str) -> List[KnowledgeSpace]:
        """Lists knowledge base namespaces inside target workspace."""
        pass

    @abstractmethod
    def create_conversation_reference(self, ref: ConversationReference) -> ConversationReference:
        """Saves conversation linkage metadata."""
        pass

    @abstractmethod
    def get_conversations(self, workspace_id: str) -> List[ConversationReference]:
        """Lists active conversation links inside workspace."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection integrity.

        Returns:
            bool: True if system is healthy.
        """
        pass


# =====================================================================
# Registry
# =====================================================================

class WorkspaceRegistry:
    """Thread-safe registry for workspace providers."""

    _instance: Optional["WorkspaceRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "WorkspaceRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._providers: Dict[str, WorkspaceProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: WorkspaceProvider) -> None:
        """Registers a WorkspaceProvider.

        Args:
            provider_id: Unique string key.
            provider: Target provider instance.
        """
        if not provider_id or not str(provider_id).strip():
            raise WorkspaceValidationError("provider_id cannot be empty.")
        if not provider:
            raise WorkspaceValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise WorkspaceValidationError(f"Provider '{provider_id}' already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"Workspace provider registered: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes workspace provider registration."""
        with self._lock:
            if provider_id not in self._providers:
                raise WorkspaceValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"Workspace provider unregistered: {provider_id}")

    def get_provider(self, provider_id: str) -> WorkspaceProvider:
        """Retrieves provider instance."""
        with self._lock:
            if provider_id not in self._providers:
                raise WorkspaceValidationError(f"Provider '{provider_id}' is not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists active provider IDs."""
        with self._lock:
            return list(self._providers.keys())

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# Context Resolver
# =====================================================================

@dataclass(frozen=True)
class ResolvedWorkspaceContext:
    """Consolidated access control scope outcome.

    Attributes:
        workspace: Resolved Workspace.
        project: Resolved Project, if requested.
        knowledge_space: Resolved KnowledgeSpace, if requested.
        member_role: Access role of target user.
        permissions: Computed explicit permissions.
        visible_resources: Extra visible resource identifiers.
    """
    workspace: Workspace
    project: Optional[Project]
    knowledge_space: Optional[KnowledgeSpace]
    member_role: WorkspaceRole
    permissions: List[str]
    visible_resources: List[str] = field(default_factory=list)


class WorkspaceContextResolver:
    """Evaluates multi-tenant access alignment and permission resolution."""

    DEFAULT_ROLE_PERMISSIONS: Dict[str, List[str]] = {
        WorkspaceRole.OWNER.value: ["READ", "WRITE", "DELETE", "ADMIN", "WORKSPACE_MANAGE"],
        WorkspaceRole.ADMIN.value: ["READ", "WRITE", "DELETE", "WORKSPACE_MANAGE"],
        WorkspaceRole.EDITOR.value: ["READ", "WRITE", "AGENT_EXECUTE"],
        WorkspaceRole.MEMBER.value: ["READ", "WRITE", "AGENT_EXECUTE"],
        WorkspaceRole.VIEWER.value: ["READ"],
    }

    def __init__(self, provider: WorkspaceProvider) -> None:
        self.provider = provider

    def resolve_context(
        self,
        user_id: str,
        workspace_id: str,
        project_id: Optional[str] = None,
        knowledge_space_id: Optional[str] = None
    ) -> ResolvedWorkspaceContext:
        """Loads and verifies that requested workspace boundaries match access.

        Args:
            user_id: Identity to query.
            workspace_id: Target workspace ID.
            project_id: Optional target project context.
            knowledge_space_id: Optional target knowledge context.

        Returns:
            ResolvedWorkspaceContext: Validated context attributes.

        Raises:
            WorkspaceNotFoundError: If workspace does not exist.
            WorkspaceValidationError: On tenant breaches or invalid resource associations.
        """
        # Resolve Workspace
        ws = self.provider.get_workspace(workspace_id)
        if not ws:
            raise WorkspaceNotFoundError(f"Workspace '{workspace_id}' not found.")

        # Archive/Delete check
        if ws.status in ("deleted", "archived") and user_id != ws.owner_id:
            # Non-owners cannot access archived or deleted workspaces
            raise WorkspaceValidationError(f"Workspace '{workspace_id}' is archived or deleted.")

        # Check user membership
        members = self.provider.get_members(workspace_id)
        user_member: Optional[WorkspaceMember] = None
        for m in members:
            if m.user_id == user_id and m.status == "active":
                user_member = m
                break

        # Check special case: owner status automatically bypasses membership list check
        if not user_member and ws.owner_id == user_id:
            user_member = WorkspaceMember(
                member_id=f"owner-{user_id}",
                workspace_id=workspace_id,
                user_id=user_id,
                role=WorkspaceRole.OWNER.value,
                joined_at=ws.created_at,
                status="active"
            )

        if not user_member:
            raise WorkspaceValidationError(f"User '{user_id}' does not have active membership in workspace '{workspace_id}'.")

        # Resolve role enum
        try:
            role_enum = WorkspaceRole(user_member.role.upper())
        except ValueError:
            role_enum = WorkspaceRole.VIEWER

        permissions = self.DEFAULT_ROLE_PERMISSIONS.get(role_enum.value, ["READ"])

        # Resolve Project context if specified
        resolved_proj = None
        if project_id:
            projects = self.provider.list_projects(workspace_id)
            for p in projects:
                if p.project_id == project_id:
                    resolved_proj = p
                    break
            if not resolved_proj:
                raise WorkspaceValidationError(f"Project '{project_id}' does not belong to workspace '{workspace_id}'.")

        # Resolve Knowledge Space context if specified
        resolved_ks = None
        if knowledge_space_id:
            spaces = self.provider.get_knowledge_spaces(workspace_id)
            for ks in spaces:
                if ks.knowledge_space_id == knowledge_space_id:
                    resolved_ks = ks
                    break
            if not resolved_ks:
                raise WorkspaceValidationError(f"KnowledgeSpace '{knowledge_space_id}' does not belong to workspace '{workspace_id}'.")

        visible_res = [workspace_id]
        if resolved_proj:
            visible_res.append(project_id)
        if resolved_ks:
            visible_res.append(knowledge_space_id)

        return ResolvedWorkspaceContext(
            workspace=ws,
            project=resolved_proj,
            knowledge_space=resolved_ks,
            member_role=role_enum,
            permissions=permissions,
            visible_resources=visible_res
        )


# =====================================================================
# Workspace Agent
# =====================================================================

class WorkspaceAgent(BaseAgent):
    """System agent governing multi-tenant resource namespaces."""

    def __init__(
        self,
        name: str = "WorkspaceAgent",
        description: str = "Manages multi-tenant workspaces, projects, spaces, and context resolution",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["WORKSPACE_MANAGEMENT", "CONTEXT_RESOLUTION"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = WorkspaceRegistry()
        self.event_bus = EventBus()

    def initialize(self) -> None:
        """Initializes Workspace agent."""
        super().initialize()

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]
        provider_id = task.metadata.get("provider_id")

        if not provider_id:
            providers = self.registry.list_providers()
            if not providers:
                raise WorkspaceValidationError("No workspace providers registered.")
            provider_id = providers[0]

        provider = self.registry.get_provider(provider_id)
        resolver = WorkspaceContextResolver(provider)

        if action == "create_workspace":
            ws_id = task.metadata.get("workspace_id") or str(uuid.uuid4())
            name = task.metadata.get("name")
            desc = task.metadata.get("description", "")
            owner_id = task.metadata.get("owner_id")
            org_id = task.metadata.get("organization_id", "default")
            req_metadata = task.metadata.get("metadata", {})

            validate_workspace_id(ws_id)
            validate_workspace_name(name)
            if not owner_id:
                raise WorkspaceValidationError("Missing owner_id parameter.")

            if provider.get_workspace(ws_id):
                raise WorkspaceValidationError(f"Workspace with ID '{ws_id}' already exists.")

            now = datetime.utcnow()
            ws = Workspace(
                workspace_id=ws_id,
                name=name,
                description=desc,
                owner_id=owner_id,
                organization_id=org_id,
                created_at=now,
                updated_at=now,
                status="active",
                metadata=req_metadata
            )
            created_ws = provider.create_workspace(ws)
            self._publish_event("workspace.created", workspace_id=ws_id, owner_id=owner_id)
            return created_ws

        elif action == "update_workspace":
            ws_id = task.metadata.get("workspace_id")
            name = task.metadata.get("name")
            desc = task.metadata.get("description")
            status = task.metadata.get("status")
            req_metadata = task.metadata.get("metadata")

            validate_workspace_id(ws_id)
            existing = provider.get_workspace(ws_id)
            if not existing:
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            now = datetime.utcnow()
            # Perform updates using replace to build updated frozen dataclass
            updates: Dict[str, Any] = {"updated_at": now}
            if name is not None:
                validate_workspace_name(name)
                updates["name"] = name
            if desc is not None:
                updates["description"] = desc
            if status is not None:
                updates["status"] = status
            if req_metadata is not None:
                updates["metadata"] = req_metadata

            import dataclasses
            updated_ws = dataclasses.replace(existing, **updates)
            saved_ws = provider.update_workspace(updated_ws)
            self._publish_event("workspace.updated", workspace_id=ws_id)
            return saved_ws

        elif action == "archive_workspace":
            ws_id = task.metadata.get("workspace_id")
            validate_workspace_id(ws_id)
            existing = provider.get_workspace(ws_id)
            if not existing:
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            import dataclasses
            updated_ws = dataclasses.replace(existing, status="archived", updated_at=datetime.utcnow())
            saved_ws = provider.update_workspace(updated_ws)
            self._publish_event("workspace.updated", workspace_id=ws_id, status="archived")
            return saved_ws

        elif action == "delete_workspace":
            ws_id = task.metadata.get("workspace_id")
            validate_workspace_id(ws_id)
            existing = provider.get_workspace(ws_id)
            if not existing:
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            success = provider.delete_workspace(ws_id)
            if success:
                self._publish_event("workspace.deleted", workspace_id=ws_id)
            return success

        elif action == "add_member":
            ws_id = task.metadata.get("workspace_id")
            user_id = task.metadata.get("user_id")
            role = task.metadata.get("role", WorkspaceRole.MEMBER.value)
            status = task.metadata.get("status", "active")
            req_metadata = task.metadata.get("metadata", {})

            validate_workspace_id(ws_id)
            if not user_id:
                raise WorkspaceValidationError("Missing user_id parameter.")
            validate_member_role(role)

            if not provider.get_workspace(ws_id):
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            # Duplicate membership check
            members = provider.get_members(ws_id)
            for m in members:
                if m.user_id == user_id:
                    raise WorkspaceValidationError(f"User '{user_id}' is already a member of workspace '{ws_id}'.")

            member = WorkspaceMember(
                member_id=str(uuid.uuid4()),
                workspace_id=ws_id,
                user_id=user_id,
                role=role.upper(),
                joined_at=datetime.utcnow(),
                status=status,
                metadata=req_metadata
            )
            saved_member = provider.add_member(member)
            self._publish_event("workspace.member.added", workspace_id=ws_id, user_id=user_id, role=role)
            return saved_member

        elif action == "remove_member":
            ws_id = task.metadata.get("workspace_id")
            user_id = task.metadata.get("user_id")

            validate_workspace_id(ws_id)
            if not user_id:
                raise WorkspaceValidationError("Missing user_id parameter.")

            ws = provider.get_workspace(ws_id)
            if not ws:
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            # Prevent removing owner
            if ws.owner_id == user_id:
                raise WorkspaceValidationError("Cannot remove workspace owner from workspace membership.")

            success = provider.remove_member(ws_id, user_id)
            if success:
                self._publish_event("workspace.member.removed", workspace_id=ws_id, user_id=user_id)
            return success

        elif action == "create_project":
            ws_id = task.metadata.get("workspace_id")
            proj_id = task.metadata.get("project_id") or str(uuid.uuid4())
            name = task.metadata.get("name")
            desc = task.metadata.get("description", "")
            req_metadata = task.metadata.get("metadata", {})

            validate_workspace_id(ws_id)
            if not name or not str(name).strip():
                raise WorkspaceValidationError("Project name cannot be empty.")

            if not provider.get_workspace(ws_id):
                raise WorkspaceNotFoundError(f"Workspace '{ws_id}' does not exist.")

            # Verify no duplicate project name inside same workspace
            existing_projects = provider.list_projects(ws_id)
            for p in existing_projects:
                if p.name.strip().lower() == name.strip().lower():
                    raise WorkspaceValidationError(f"Project '{name}' already exists in workspace '{ws_id}'.")

            proj = Project(
                project_id=proj_id,
                workspace_id=ws_id,
                name=name,
                description=desc,
                created_at=datetime.utcnow(),
                metadata=req_metadata
            )
            created_proj = provider.create_project(proj)
            self._publish_event("workspace.project.created", workspace_id=ws_id, project_id=proj_id)
            return created_proj

        elif action == "resolve_context":
            user_id = task.metadata.get("user_id")
            ws_id = task.metadata.get("workspace_id")
            proj_id = task.metadata.get("project_id")
            ks_id = task.metadata.get("knowledge_space_id")

            if not user_id or not ws_id:
                raise WorkspaceValidationError("Missing user_id or workspace_id parameters for context resolution.")

            resolved = resolver.resolve_context(
                user_id=user_id,
                workspace_id=ws_id,
                project_id=proj_id,
                knowledge_space_id=ks_id
            )
            self._publish_event("workspace.context.resolved", workspace_id=ws_id, user_id=user_id)
            return resolved

        else:
            raise WorkspaceValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkspaceAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
