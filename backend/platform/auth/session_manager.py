"""Session manager module for tracking active user login sessions."""

import threading
import time
from typing import Dict, List, Optional


class SessionManager:
    """Manages active user session lifecycle details."""

    def __init__(self, session_expiry_seconds: int = 1800) -> None:
        """Initializes the Session Manager.

        Args:
            session_expiry_seconds: Session timeout length in seconds (default 30 mins).
        """
        self.session_expiry = session_expiry_seconds
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, user_id: str, client_ip: Optional[str] = None) -> bool:
        """Creates an active session for a user.

        Args:
            session_id: Unique session ID/token.
            user_id: ID of the user.
            client_ip: Optional remote IP of the client.

        Returns:
            True if session created.
        """
        expires_at = int(time.time()) + self.session_expiry
        with self._lock:
            self._sessions[session_id] = {
                "user_id": user_id,
                "expires_at": expires_at,
                "client_ip": client_ip,
                "last_active": int(time.time())
            }
        return True

    def validate_session(self, session_id: str) -> Optional[str]:
        """Validates a session, updating its activity timestamp if valid.

        Args:
            session_id: Unique session ID to validate.

        Returns:
            user_id if session is valid and active, otherwise None.
        """
        with self._lock:
            sess = self._sessions.get(session_id)
            if not sess:
                return None
            now = int(time.time())
            if now > sess["expires_at"]:
                self._sessions.pop(session_id, None)
                return None
            
            # Slide expiration window
            sess["last_active"] = now
            sess["expires_at"] = now + self.session_expiry
            return sess["user_id"]

    def destroy_session(self, session_id: str) -> bool:
        """Destroys an active session.

        Args:
            session_id: Session identifier to terminate.

        Returns:
            True if session was terminated, False if it didn't exist.
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def list_user_sessions(self, user_id: str) -> List[str]:
        """Lists active session IDs for a specific user.

        Args:
            user_id: User identifier.

        Returns:
            List of session IDs.
        """
        with self._lock:
            now = int(time.time())
            active = []
            for sid, s in list(self._sessions.items()):
                if s["user_id"] == user_id:
                    if now <= s["expires_at"]:
                        active.append(sid)
                    else:
                        self._sessions.pop(sid, None)
            return active
