"""Refresh token management module."""

import secrets
import threading
import time
from typing import Dict, Optional


class RefreshTokenManager:
    """Manages generation, storage, and revocation of refresh tokens in a thread-safe manner."""

    def __init__(self, expiry_seconds: int = 2592000) -> None:  # Default 30 days
        """Initializes the Refresh Token Manager.

        Args:
            expiry_seconds: Lifecycle of refresh token in seconds.
        """
        self.expiry_seconds = expiry_seconds
        self._tokens: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_token(self, user_id: str) -> str:
        """Generates a secure refresh token for a user.

        Args:
            user_id: ID of the user.

        Returns:
            The generated token string.
        """
        token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + self.expiry_seconds
        with self._lock:
            self._tokens[token] = {
                "user_id": user_id,
                "expires_at": expires_at,
                "revoked": False
            }
        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Validates a refresh token and returns the corresponding user_id.

        Args:
            token: The refresh token to check.

        Returns:
            user_id if valid and not expired, otherwise None.
        """
        with self._lock:
            info = self._tokens.get(token)
            if not info:
                return None
            if info["revoked"]:
                return None
            if int(time.time()) > info["expires_at"]:
                return None
            return info["user_id"]

    def revoke_token(self, token: str) -> bool:
        """Revokes a refresh token.

        Args:
            token: The refresh token to revoke.

        Returns:
            True if revoked successfully, False if token did not exist.
        """
        with self._lock:
            info = self._tokens.get(token)
            if not info:
                return False
            info["revoked"] = True
            return True
