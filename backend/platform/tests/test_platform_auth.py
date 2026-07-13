"""Unit tests for Platform Authentication and Authorization modules."""

import time
import unittest

from backend.platform.auth.password_manager import PasswordManager
from backend.platform.auth.jwt_manager import JWTManager
from backend.platform.auth.refresh_tokens import RefreshTokenManager
from backend.platform.auth.session_manager import SessionManager
from backend.platform.auth.authorization import AuthorizationService
from backend.platform.auth.oauth_provider import GitHubOAuthProvider


class TestPlatformAuth(unittest.TestCase):
    """Test suite covering credentials, JWT validation, sessions, and access lists."""

    def test_password_manager(self) -> None:
        """Verifies password hashing and verification match checks."""
        pm = PasswordManager(iterations=1000)  # low iterations for fast test
        pw = "my-secret-password"
        hashed = pm.hash_password(pw)
        self.assertNotEqual(pw, hashed)
        self.assertTrue(pm.verify_password(pw, hashed))
        self.assertFalse(pm.verify_password("wrong-password", hashed))

    def test_jwt_manager(self) -> None:
        """Verifies JWT token encoding, signature, and expiration rules."""
        jwt = JWTManager(secret_key="my-super-secret", default_expiry_seconds=2)
        payload = {"sub": "user-123", "role": "admin"}
        token = jwt.encode(payload)
        
        # Valid decode
        decoded = jwt.decode(token)
        self.assertEqual(decoded["sub"], "user-123")
        
        # Expired token
        expired_payload = {"sub": "user-123", "role": "admin", "exp": int(time.time()) - 10}
        expired_token = jwt.encode(expired_payload)
        with self.assertRaises(ValueError):
            jwt.decode(expired_token)

    def test_refresh_tokens(self) -> None:
        """Verifies refresh token issuance, verification, and revocation."""
        rt = RefreshTokenManager(expiry_seconds=5)
        token = rt.create_token("user-456")
        
        # Valid check
        self.assertEqual(rt.verify_token(token), "user-456")
        
        # Revoke token
        rt.revoke_token(token)
        self.assertIsNone(rt.verify_token(token))

    def test_session_manager(self) -> None:
        """Verifies session lifecycle, sliding window, and listing."""
        sm = SessionManager(session_expiry_seconds=3)
        self.assertTrue(sm.create_session("session-abc", "user-789"))
        self.assertEqual(sm.validate_session("session-abc"), "user-789")
        
        # Invalid session
        self.assertIsNone(sm.validate_session("session-xyz"))
        
        # List active sessions
        sessions = sm.list_user_sessions("user-789")
        self.assertIn("session-abc", sessions)

    def test_authorization_rbac(self) -> None:
        """Verifies RBAC rules and dynamic permission registration."""
        auth = AuthorizationService()
        self.assertTrue(auth.has_permission("admin", "workspace:write"))
        self.assertFalse(auth.has_permission("viewer", "workspace:write"))
        
        # Test permission inheritance (owner inherits member/viewer permissions)
        self.assertTrue(auth.has_permission("owner", "data:read"))
        self.assertTrue(auth.has_permission("admin", "data:read"))

        # Register custom permission
        auth.add_role_permission("viewer", "custom:read")
        self.assertTrue(auth.has_permission("viewer", "custom:read"))

    def test_github_oauth_flow(self) -> None:
        """Verifies GitHub OAuth state URLs construction and exchange mocks."""
        oauth = GitHubOAuthProvider("github", "client-id", "client-secret", "http://callback")
        url = oauth.get_authorization_url("state-token")
        self.assertIn("state-token", url)
        
        tokens = oauth.exchange_code_for_token("code-123")
        self.assertEqual(tokens["access_token"], "github_access_token_code-123")
        
        profile = oauth.get_user_profile(tokens["access_token"])
        self.assertEqual(profile["login"], "oauth_github_user")
