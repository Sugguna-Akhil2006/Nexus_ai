"""Team manager module for creating, updating, and managing teams within organizations."""

import threading
from typing import Dict, List, Any, Optional


class TeamManager:
    """Manages team structures, members, and access properties."""

    def __init__(self) -> None:
        """Initializes internal storage mappings."""
        self._teams: Dict[str, Dict[str, Any]] = {}
        # maps team_id -> Dict[user_id, role]
        self._team_members: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()

    def create_team(self, team_id: str, org_id: str, name: str) -> Dict[str, Any]:
        """Creates a team under an organization.

        Args:
            team_id: Unique ID of the team.
            org_id: Organization ID.
            name: Team name.
        """
        with self._lock:
            if team_id in self._teams:
                raise ValueError("Team already exists")
            team = {
                "team_id": team_id,
                "org_id": org_id,
                "name": name,
            }
            self._teams[team_id] = team
            self._team_members[team_id] = {}
            return team

    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves team details."""
        with self._lock:
            return self._teams.get(team_id)

    def update_team(self, team_id: str, name: str) -> bool:
        """Updates team details."""
        with self._lock:
            team = self._teams.get(team_id)
            if not team:
                return False
            team["name"] = name
            return True

    def delete_team(self, team_id: str) -> bool:
        """Deletes a team."""
        with self._lock:
            if team_id in self._teams:
                del self._teams[team_id]
                self._team_members.pop(team_id, None)
                return True
            return False

    def add_member(self, team_id: str, user_id: str, role: str = "member") -> bool:
        """Adds a member to a team."""
        with self._lock:
            if team_id not in self._teams:
                return False
            self._team_members[team_id][user_id] = role
            return True

    def remove_member(self, team_id: str, user_id: str) -> bool:
        """Removes a member from a team."""
        with self._lock:
            if team_id not in self._team_members or user_id not in self._team_members[team_id]:
                return False
            del self._team_members[team_id][user_id]
            return True

    def get_members(self, team_id: str) -> Dict[str, str]:
        """Returns all members and roles for a team."""
        with self._lock:
            return dict(self._team_members.get(team_id, {}))
