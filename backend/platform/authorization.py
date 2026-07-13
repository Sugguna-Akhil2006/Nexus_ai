"""Authorization module establishing Role-Based Access Control (RBAC)."""

from typing import Dict, List, Set


class AuthorizationService:
    """Manages role-to-permission mappings and evaluates access policy permissions."""

    def __init__(self) -> None:
        """Initializes RBAC mappings with default permissions."""
        self._role_permissions: Dict[str, Set[str]] = {
            "owner": {
                "workspace:read", "workspace:write", "workspace:delete",
                "member:add", "member:remove", "member:edit",
                "org:admin", "data:read", "data:write", "data:delete"
            },
            "admin": {
                "workspace:read", "workspace:write",
                "member:add", "member:remove", "member:edit",
                "data:read", "data:write", "data:delete"
            },
            "member": {
                "workspace:read", "workspace:write",
                "data:read", "data:write"
            },
            "viewer": {
                "workspace:read",
                "data:read"
            }
        }

    def add_role_permission(self, role: str, permission: str) -> None:
        """Dynamically registers a permission for a role.

        Args:
            role: Target role string.
            permission: Specific permission token.
        """
        role = role.lower()
        if role not in self._role_permissions:
            self._role_permissions[role] = set()
        self._role_permissions[role].add(permission)

    def has_permission(self, role: str, permission: str) -> bool:
        """Determines if a role carries a specific permission.

        Args:
            role: The user's role.
            permission: The permission key to check.

        Returns:
            True if permitted, False otherwise.
        """
        role = role.lower()
        permissions = self._role_permissions.get(role)
        if not permissions:
            return False
        return permission in permissions
