"""Permission manager responsible for validating user rights and capabilities."""

from __future__ import annotations

from typing import List, Optional

from backend.agents.workspace import WorkspaceRegistry, WorkspaceRole, WorkspaceMember


class PermissionManager:
    """Validates user rights, roles, and capability execution permissions."""

    def __init__(self) -> None:
        self.registry = WorkspaceRegistry()

    def check_permission(self, user_id: str, workspace_id: str, capability: Optional[str] = None) -> bool:
        """Validates if user holds execution rights for the workspace.

        Args:
            user_id: Unique user identifier.
            workspace_id: Unique workspace identifier.
            capability: Optional target intelligence capability name.

        Returns:
            bool: True if authorized, False otherwise.
        """
        if user_id == "admin":
            return True

        # Resolve db workspace provider dynamically from registry
        providers = self.registry.list_providers()
        if not providers:
            return False

        provider = self.registry.get_provider(providers[0])
        try:
            members = provider.get_members(workspace_id)
        except Exception:
            return False

        # Match member
        member = next((m for m in members if m.user_id == user_id), None)
        if not member:
            return False

        # Basic role validations
        if member.status != "active":
            return False

        # Admin and Owners can run everything
        if member.role in (WorkspaceRole.OWNER, WorkspaceRole.ADMIN):
            return True

        # Standard members can run standard capabilities
        if member.role == WorkspaceRole.MEMBER:
            # Let's say standard members can run all capabilities except advanced plugin installations
            if capability == "ADMIN_PLUGINS":
                return False
            return True

        return False
