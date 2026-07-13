"""Authentication service module coordinating user registration and logins."""

from datetime import datetime
from typing import Dict, Any, Optional

from backend.platform.auth.password_manager import PasswordManager
from backend.platform.auth.jwt_manager import JWTManager
from backend.platform.auth.refresh_tokens import RefreshTokenManager


class AuthenticationService:
    """Orchestrates identity checks, token validation, and password compliance checks."""

    def __init__(self, jwt_manager: JWTManager, refresh_token_manager: RefreshTokenManager) -> None:
        """Initializes the Authentication Service.

        Args:
            jwt_manager: Manager for issuing access tokens.
            refresh_token_manager: Manager for issuing refresh tokens.
        """
        self.password_manager = PasswordManager()
        self.jwt_manager = jwt_manager
        self.refresh_token_manager = refresh_token_manager
        self._lockout_threshold = 5
        self._failed_attempts: Dict[str, int] = {}

    def is_account_locked(self, username: str) -> bool:
        """Checks if a user account is locked due to consecutive login failures."""
        return self._failed_attempts.get(username, 0) >= self._lockout_threshold

    def record_failed_login(self, username: str) -> None:
        """Records a failed login attempt for a user."""
        self._failed_attempts[username] = self._failed_attempts.get(username, 0) + 1

    def reset_failed_logins(self, username: str) -> None:
        """Resets failed login attempts count for a user."""
        self._failed_attempts.pop(username, None)

    def trigger_password_reset(self, username: str, new_password: str) -> str:
        """Generates a new password hash for a password reset request."""
        return self.password_manager.hash_password(new_password)

    def trigger_email_verification(self, email: str) -> bool:
        """Triggers email verification hook and returns status (simulated success)."""
        return True

    def register(self, username: str, password: str, email: str) -> Dict[str, Any]:
        """Registers a user by hashing their password.

        Args:
            username: Target user login name.
            password: Plaintext password.
            email: Primary contact email.

        Returns:
            A metadata dict containing user details.
        """
        password_hash = self.password_manager.hash_password(password)
        return {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "role": "member",
            "created_at": datetime.utcnow().isoformat()
        }

    def authenticate_credentials(self, password: str, stored_hash: str) -> bool:
        """Compares a password attempt against stored hash.

        Args:
            password: Plaintext password attempt.
            stored_hash: Secure hashed password.

        Returns:
            True if matching, False otherwise.
        """
        return self.password_manager.verify_password(password, stored_hash)

    def issue_tokens(self, user_id: str, username: str, role: str) -> Dict[str, Any]:
        """Generates an access token and a refresh token for a verified user.

        Args:
            user_id: Unique user identifier.
            username: User name.
            role: Assigned authorization role.

        Returns:
            Dict containing access token and refresh token details.
        """
        payload = {
            "sub": user_id,
            "username": username,
            "role": role
        }
        access_token = self.jwt_manager.encode(payload)
        refresh_token = self.refresh_token_manager.create_token(user_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    def refresh_access_token(self, refresh_token: str, username: str, role: str) -> Optional[str]:
        """Validates a refresh token and issues a new short-lived access token.

        Args:
            refresh_token: Token to verify.
            username: Current user login name.
            role: Current user permission level.

        Returns:
            A new JWT string if successful, otherwise None.
        """
        user_id = self.refresh_token_manager.verify_token(refresh_token)
        if not user_id:
            return None
        
        payload = {
            "sub": user_id,
            "username": username,
            "role": role
        }
        return self.jwt_manager.encode(payload)
