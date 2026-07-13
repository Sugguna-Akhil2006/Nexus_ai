"""Permission manager to handle resource-specific scopes and action mappings."""

from typing import Dict, Set, List


class PermissionManager:
    """Manages system permission tokens and resource-level capability models."""

    def __init__(self) -> None:
        """Initializes default permission boundaries."""
        self._all_permissions: Set[str] = {
            "org:read", "org:write", "org:delete",
            "team:read", "team:write", "team:delete",
            "workspace:read", "workspace:write", "workspace:delete",
            "member:add", "member:remove", "member:edit",
            "data:read", "data:write", "data:delete"
        }

    def register_permission(self, permission: str) -> bool:
        """Registers a new permission string in the system catalog.

        Args:
            permission: Unique permission string.

        Returns:
            True if newly registered, False if already registered.
        """
        if permission in self._all_permissions:
            return False
        self._all_permissions.add(permission)
        return True

    def validate_permission(self, permission: str) -> bool:
        """Checks if a permission is registered.

        Args:
            permission: The permission key.
        """
        return permission in self._all_permissions

    def list_permissions(self) -> List[str]:
        """Lists all system-registered permissions."""
        return sorted(list(self._all_permissions))
