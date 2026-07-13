"""Organization manager module handles CRUD on Organization objects and memberships."""

import threading
from typing import Dict, List, Any, Optional


class OrganizationManager:
    """Manages CRUD operations and memberships for Organizations."""

    def __init__(self) -> None:
        """Initializes storage for organizations and member associations."""
        self._organizations: Dict[str, Dict[str, Any]] = {}
        # maps org_id -> Dict[user_id, role]
        self._org_members: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()

    def create_organization(self, org_id: str, name: str, owner_id: str) -> Dict[str, Any]:
        """Creates a new organization.

        Args:
            org_id: Unique ID of the organization.
            name: Human-friendly name.
            owner_id: Primary owner user ID.
        """
        with self._lock:
            if org_id in self._organizations:
                raise ValueError("Organization already exists")
            org = {
                "org_id": org_id,
                "name": name,
                "owner_id": owner_id,
                "status": "active"
            }
            self._organizations[org_id] = org
            self._org_members[org_id] = {owner_id: "owner"}
            return org

    def get_organization(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves organization details."""
        with self._lock:
            return self._organizations.get(org_id)

    def update_organization(self, org_id: str, name: Optional[str] = None, status: Optional[str] = None) -> bool:
        """Updates organization details."""
        with self._lock:
            org = self._organizations.get(org_id)
            if not org:
                return False
            if name is not None:
                org["name"] = name
            if status is not None:
                org["status"] = status
            return True

    def delete_organization(self, org_id: str) -> bool:
        """Deletes an organization."""
        with self._lock:
            if org_id in self._organizations:
                del self._organizations[org_id]
                self._org_members.pop(org_id, None)
                return True
            return False

    def add_member(self, org_id: str, user_id: str, role: str = "member") -> bool:
        """Adds a member to an organization."""
        with self._lock:
            if org_id not in self._organizations:
                return False
            self._org_members[org_id][user_id] = role
            return True

    def remove_member(self, org_id: str, user_id: str) -> bool:
        """Removes a member from an organization."""
        with self._lock:
            if org_id not in self._org_members or user_id not in self._org_members[org_id]:
                return False
            del self._org_members[org_id][user_id]
            return True

    def get_members(self, org_id: str) -> Dict[str, str]:
        """Returns all members and roles for an organization."""
        with self._lock:
            return dict(self._org_members.get(org_id, {}))
