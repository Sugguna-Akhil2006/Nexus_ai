"""Cross-Site Request Forgery (CSRF) token generation and verification."""

import secrets
from typing import Dict, Any, Optional


class CSRFProtector:
    """Manages secure token generation and validation against request contexts."""

    def __init__(self, token_name: str = "csrf_token") -> None:
        """Initializes settings.

        Args:
            token_name: Header/cookie key.
        """
        self.token_name = token_name

    def generate_token(self) -> str:
        """Generates a secure cryptographically random token."""
        return secrets.token_hex(32)

    def verify_token(self, request_token: Optional[str], session_token: Optional[str]) -> bool:
        """Compares request header token against session token.

        Args:
            request_token: Header or form token received.
            session_token: Stored session cookie value.
        """
        if not request_token or not session_token:
            return False
        return secrets.compare_digest(request_token, session_token)
