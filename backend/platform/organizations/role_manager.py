"""Role manager to define, update, and manage role-to-permission mapping scopes."""

import threading
from typing import Dict, Set, List, Optional


class RoleManager:
    """Manages role-to-permission mappings in a thread-safe registry."""

    def __init__(self) -> None:
        """Initializes default roles and permissions."""
        self._lock = threading.Lock()
        self._roles: Dict[str, Set[str]] = {
            "owner": {
                "org:read", "org:write", "org:delete",
                "team:read", "team:write", "team:delete",
                "workspace:read", "workspace:write", "workspace:delete",
                "member:add", "member:remove", "member:edit",
                "data:read", "data:write", "data:delete"
            },
            "admin": {
                "org:read", "org:write",
                "team:read", "team:write", "team:delete",
                "workspace:read", "workspace:write",
                "member:add", "member:remove", "member:edit",
                "data:read", "data:write", "data:delete"
            },
            "member": {
                "org:read",
                "team:read",
                "workspace:read", "workspace:write",
                "data:read", "data:write"
            },
            "viewer": {
                "org:read",
                "team:read",
                "workspace:read",
                "data:read"
            }
        }

    def create_role(self, role_name: str, permissions: Optional[Set[str]] = None) -> bool:
        """Creates a new role definition.

        Args:
            role_name: Unique role name.
            permissions: Optional set of initial permissions.
        """
        role_name = role_name.lower().strip()
        with self._lock:
            if role_name in self._roles:
                return False
            self._roles[role_name] = permissions or set()
            return True

    def assign_permissions_to_role(self, role_name: str, permissions: List[str]) -> bool:
        """Assigns permissions to a role.

        Args:
            role_name: Role to assign to.
            permissions: List of permission keys.
        """
        role_name = role_name.lower().strip()
        with self._lock:
            if role_name not in self._roles:
                return False
            self._roles[role_name].update(permissions)
            return True

    def get_role_permissions(self, role_name: str) -> Optional[Set[str]]:
        """Retrieves permissions for a role."""
        role_name = role_name.lower().strip()
        with self._lock:
            role_perms = self._roles.get(role_name)
            if role_perms is None:
                return None
            return set(role_perms)
