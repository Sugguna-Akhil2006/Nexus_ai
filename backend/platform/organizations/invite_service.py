"""Invite service module to issue and process invitations for organizations/teams."""

import secrets
import threading
import time
from typing import Dict, Any, Optional


class InviteService:
    """Manages invitation link states, verification tokens, and acceptances."""

    def __init__(self, token_expiry_seconds: int = 86400 * 7) -> None:  # Default 7 days
        """Initializes the Invite Service.

        Args:
            token_expiry_seconds: Lifecycle of invitation token in seconds.
        """
        self.token_expiry = token_expiry_seconds
        self._invites: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_invite(
        self,
        email: str,
        org_id: str,
        role: str = "member",
        team_id: Optional[str] = None
    ) -> str:
        """Creates an invitation for an email.

        Args:
            email: Recipient email address.
            org_id: Organization ID being invited to.
            role: Target role to grant on acceptance.
            team_id: Optional team ID to automatically join.

        Returns:
            A unique secure token.
        """
        token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + self.token_expiry
        with self._lock:
            self._invites[token] = {
                "email": email,
                "org_id": org_id,
                "role": role,
                "team_id": team_id,
                "expires_at": expires_at,
                "accepted": False
            }
        return token

    def validate_invite(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifies if an invitation token is active and valid.

        Args:
            token: Invite verification token.

        Returns:
            The invite payload if valid, otherwise None.
        """
        with self._lock:
            invite = self._invites.get(token)
            if not invite:
                return None
            if invite["accepted"]:
                return None
            if int(time.time()) > invite["expires_at"]:
                return None
            return dict(invite)

    def accept_invite(self, token: str, user_email: str) -> Optional[Dict[str, Any]]:
        """Accepts the invite, updating status to accepted.

        Args:
            token: Verification token.
            user_email: The email of the accepting user (must match the invite).
        """
        with self._lock:
            invite = self._invites.get(token)
            if not invite:
                return None
            if invite["accepted"]:
                return None
            if int(time.time()) > invite["expires_at"]:
                return None
            if invite["email"].lower() != user_email.lower():
                return None

            invite["accepted"] = True
            return dict(invite)
