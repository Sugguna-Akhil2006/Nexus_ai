"""Authorization module establishing Role-Based Access Control (RBAC)."""

from typing import Dict, Set


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

        self._role_hierarchy: Dict[str, list[str]] = {
            "owner": ["admin"],
            "admin": ["member"],
            "member": ["viewer"],
            "viewer": []
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

    def get_all_role_permissions(self, role: str) -> Set[str]:
        """Resolves all permissions for a role, including inherited permissions.

        Args:
            role: Target role string.
        """
        role = role.lower()
        perms = set(self._role_permissions.get(role, []))
        
        # Traverse hierarchy
        parents = self._role_hierarchy.get(role, [])
        for p in parents:
            perms.update(self.get_all_role_permissions(p))
        return perms

    def has_permission(self, role: str, permission: str) -> bool:
        """Determines if a role carries a specific permission, considering inheritance.

        Args:
            role: The user's role.
            permission: The permission key to check.

        Returns:
            True if permitted, False otherwise.
        """
        all_perms = self.get_all_role_permissions(role)
        return permission in all_perms
