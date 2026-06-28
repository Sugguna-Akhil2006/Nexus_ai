import concurrent.futures
from datetime import datetime, timedelta
import threading
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.agents.auth import (
    AuthError,
    AuthValidationError,
    AuthorizationError,
    SessionExpiredError,
    Permission,
    UserIdentity,
    AuthRequest,
    AuthResponse,
    SessionInfo,
    AuthenticationProvider,
    AuthenticationRegistry,
    AuthorizationPolicy,
    DefaultAuthorizationPolicy,
    CompositeAuthorizationPolicy,
    PolicyCompositionStrategy,
    AuthenticationAgent,
    validate_username,
    validate_email,
    validate_role,
    validate_permission,
)
from backend.runtime.base import AgentState, AgentStatus
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class MockJWTProvider(AuthenticationProvider):
    """Mock identity provider for unit tests."""

    def __init__(self) -> None:
        self.revoked_tokens = set()
        self.health_healthy = True

    def authenticate(self, request: AuthRequest) -> AuthResponse:
        if request.credential == "correct-secret":
            identity = UserIdentity(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                display_name="Test User",
                tenant_id=request.workspace,
                roles=["developer"],
                permissions=["READ", "WRITE"],
                status="active"
            )
            issued = {
                "access_token": f"access-{request.request_id}",
                "refresh_token": f"refresh-{request.request_id}"
            }
            return AuthResponse(
                authenticated=True,
                identity=identity,
                issued_tokens=issued,
                expiration=datetime.utcnow() + timedelta(hours=1)
            )
        return AuthResponse(authenticated=False, identity=None)

    def validate_token(self, token: str, workspace: Optional[str] = None) -> UserIdentity:
        if token in self.revoked_tokens:
            raise AuthValidationError("Token revoked.")
        if token.startswith("access-") or token == "valid-direct-token":
            return UserIdentity(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                display_name="Test User",
                tenant_id=workspace or "workspace_1",
                roles=["developer"],
                permissions=["READ", "WRITE"],
                status="active"
            )
        raise AuthValidationError("Invalid token signature.")

    def refresh(self, refresh_token: str) -> AuthResponse:
        if refresh_token.startswith("refresh-") or refresh_token == "valid-refresh":
            identity = UserIdentity(
                user_id="user_123",
                username="testuser",
                email="test@example.com",
                display_name="Test User",
                tenant_id="workspace_1",
                roles=["developer"],
                permissions=["READ", "WRITE"],
                status="active"
            )
            issued = {
                "access_token": "access-new-refreshed",
                "refresh_token": "refresh-new-refreshed"
            }
            return AuthResponse(
                authenticated=True,
                identity=identity,
                issued_tokens=issued,
                expiration=datetime.utcnow() + timedelta(hours=1)
            )
        raise AuthValidationError("Invalid refresh token.")

    def revoke(self, token: str) -> bool:
        self.revoked_tokens.add(token)
        return True

    def health_check(self) -> bool:
        return self.health_healthy


class TestAuthenticationSystem(unittest.TestCase):
    """Suite of tests covering the Authentication/Authorization system."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        # Clear Registry singleton cache
        self.registry = AuthenticationRegistry()
        with self.registry._lock:
            self.registry._providers.clear()
            self.registry._sessions.clear()

        self.provider = MockJWTProvider()
        self.registry.register_provider("jwt", self.provider)

        # Setup agent
        self.agent = AuthenticationAgent()
        self.agent.initialize()

    def test_validation_utilities(self) -> None:
        """Verifies syntax validations for usernames, emails, and roles."""
        # Valid
        validate_username("valid_user")
        validate_username("user.name@example")
        validate_email("user@example.com")
        validate_role("developer")
        validate_permission(Permission.READ)
        validate_permission("READ")

        # Invalid usernames
        with self.assertRaises(AuthValidationError):
            validate_username("ab")  # Too short
        with self.assertRaises(AuthValidationError):
            validate_username("user$name")  # Invalid chars

        # Invalid emails
        with self.assertRaises(AuthValidationError):
            validate_email("invalid-email")
        with self.assertRaises(AuthValidationError):
            validate_email("user@")

        # Invalid roles
        with self.assertRaises(AuthValidationError):
            validate_role("")

    def test_identity_immutability(self) -> None:
        """Verifies UserIdentity fields are immutable."""
        identity = UserIdentity(
            user_id="1", username="u", email="e", display_name="d",
            tenant_id="t", roles=[], permissions=[], status="active"
        )
        with self.assertRaises(AttributeError):
            identity.username = "new"  # type: ignore

    def test_registry_singleton(self) -> None:
        """Verifies AuthenticationRegistry adheres to Singleton pattern."""
        registry2 = AuthenticationRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration_failures(self) -> None:
        """Verifies validations enforce provider registration constraints."""
        with self.assertRaises(AuthValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(AuthValidationError):
            self.registry.register_provider("jwt2", None)  # type: ignore
        with self.assertRaises(AuthValidationError):
            self.registry.register_provider("jwt", self.provider)  # Duplicate

    def test_unregistration(self) -> None:
        """Verifies unregistering a provider behaves correctly."""
        self.registry.unregister_provider("jwt")
        self.assertNotIn("jwt", self.registry.list_providers())
        with self.assertRaises(AuthValidationError):
            self.registry.unregister_provider("jwt")

    def test_authenticate_success(self) -> None:
        """Verifies successful provider authentication creates session."""
        req = AuthRequest(
            request_id="req-1",
            credential_type="token",
            credential="correct-secret",
            workspace="workspace_1"
        )
        res = self.registry.authenticate("jwt", req)
        self.assertTrue(res.authenticated)
        self.assertIsNotNone(res.identity)
        self.assertEqual(res.identity.user_id, "user_123")

        # Check session was registered
        access_token = res.issued_tokens["access_token"]
        session = self.registry._sessions[access_token]
        self.assertEqual(session.user_id, "user_123")
        self.assertEqual(session.metadata["workspace"], "workspace_1")

    def test_authenticate_failed(self) -> None:
        """Verifies failed authentication returns unauthenticated response."""
        req = AuthRequest(
            request_id="req-2",
            credential_type="token",
            credential="wrong-secret",
            workspace="workspace_1"
        )
        res = self.registry.authenticate("jwt", req)
        self.assertFalse(res.authenticated)
        self.assertNotIn("access-req-2", self.registry._sessions)

    def test_session_lifecycle_and_expiration(self) -> None:
        """Verifies session expiration validations."""
        now = datetime.utcnow()
        session = SessionInfo(
            session_id="access-abc",
            user_id="user_123",
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(seconds=1),
            last_activity=now - timedelta(hours=2),
            device_info="test",
            ip_address="127.0.0.1",
            metadata={"provider_id": "jwt", "workspace": "workspace_1"}
        )
        self.registry._sessions["access-abc"] = session

        # Verify validation fails on expired session
        with self.assertRaises(SessionExpiredError):
            self.registry.validate("access-abc", "workspace_1")

        # Active session validation
        session2 = SessionInfo(
            session_id="access-xyz",
            user_id="user_123",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_activity=now,
            device_info="test",
            ip_address="127.0.0.1",
            metadata={"provider_id": "jwt", "workspace": "workspace_1"}
        )
        self.registry._sessions["access-xyz"] = session2
        identity = self.registry.validate("access-xyz", "workspace_1")
        self.assertEqual(identity.user_id, "user_123")
        # Ensure last activity updated
        self.assertGreater(session2.last_activity, now - timedelta(seconds=5))

    def test_tenant_isolation_checks(self) -> None:
        """Verifies session validation checks for matching workspaces."""
        now = datetime.utcnow()
        session = SessionInfo(
            session_id="token-abc",
            user_id="user_123",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_activity=now,
            device_info="test",
            ip_address="127.0.0.1",
            metadata={"provider_id": "jwt", "workspace": "workspace_1"}
        )
        self.registry._sessions["token-abc"] = session

        # Mismatched workspace query should fail validation
        with self.assertRaises(AuthorizationError):
            self.registry.validate("token-abc", "workspace_mismatch")

    def test_direct_validation_without_session(self) -> None:
        """Verifies validation falls back to trying registered providers."""
        identity = self.registry.validate("valid-direct-token", "workspace_1")
        self.assertEqual(identity.user_id, "user_123")
        # Validate session was dynamically cached
        self.assertIn("valid-direct-token", self.registry._sessions)

    def test_refresh_lifecycle(self) -> None:
        """Verifies refreshing tokens updates session credentials."""
        req = AuthRequest(
            request_id="req-1",
            credential_type="token",
            credential="correct-secret",
            workspace="workspace_1"
        )
        res = self.registry.authenticate("jwt", req)
        access_tok = res.issued_tokens["access_token"]
        refresh_tok = res.issued_tokens["refresh_token"]

        self.assertIn(access_tok, self.registry._sessions)

        # Refresh
        res_refreshed = self.registry.refresh("jwt", refresh_tok)
        new_access = res_refreshed.issued_tokens["access_token"]

        # Cache must now contain new access token
        self.assertIn(new_access, self.registry._sessions)

    def test_revocation(self) -> None:
        """Verifies revoking a session deletes cached state."""
        req = AuthRequest(
            request_id="req-1",
            credential_type="token",
            credential="correct-secret",
            workspace="workspace_1"
        )
        res = self.registry.authenticate("jwt", req)
        tok = res.issued_tokens["access_token"]

        self.registry.revoke(tok)
        self.assertNotIn(tok, self.registry._sessions)
        self.assertIn(tok, self.provider.revoked_tokens)

    def test_health_check(self) -> None:
        """Verifies health check query routes status."""
        health = self.registry.health_check()
        self.assertTrue(health["jwt"])
        self.provider.health_healthy = False
        health = self.registry.health_check()
        self.assertFalse(health["jwt"])

    def test_authorization_rbac_policy(self) -> None:
        """Verifies RBAC evaluation rules."""
        policy = DefaultAuthorizationPolicy()
        identity = UserIdentity(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            tenant_id="workspace_1",
            roles=["viewer"],
            permissions=["WRITE"],
            status="active"
        )

        # Viewer role has READ permission
        self.assertTrue(policy.evaluate(identity, "READ", context={"workspace": "workspace_1"}))
        # Explicit permissions allow WRITE
        self.assertTrue(policy.evaluate(identity, "WRITE", context={"workspace": "workspace_1"}))
        # Viewer doesn't have DELETE
        self.assertFalse(policy.evaluate(identity, "DELETE", context={"workspace": "workspace_1"}))

        # Tenant breach context
        self.assertFalse(policy.evaluate(identity, "READ", context={"workspace": "workspace_breach"}))

        # Admin overrides
        admin_identity = UserIdentity(
            user_id="admin_123",
            username="admin",
            email="admin@example.com",
            display_name="Admin",
            tenant_id="workspace_1",
            roles=["admin"],
            permissions=[],
            status="active"
        )
        self.assertTrue(policy.evaluate(admin_identity, "DELETE", context={"workspace": "workspace_1"}))

    def test_composite_policy(self) -> None:
        """Verifies AND/OR policy composition strategies."""
        class TruePolicy(AuthorizationPolicy):
            def evaluate(self, identity, permission, resource=None, context=None):
                return True

        class FalsePolicy(AuthorizationPolicy):
            def evaluate(self, identity, permission, resource=None, context=None):
                return False

        identity = UserIdentity(
            user_id="user_123",
            username="testuser",
            email="test@example.com",
            display_name="Test User",
            tenant_id="workspace_1",
            roles=["viewer"],
            permissions=[],
            status="active"
        )

        # ALL_MUST_PASS logic
        and_policy = CompositeAuthorizationPolicy(
            [TruePolicy(), FalsePolicy()],
            strategy=PolicyCompositionStrategy.ALL_MUST_PASS
        )
        self.assertFalse(and_policy.evaluate(identity, "READ"))

        # ANY_MUST_PASS logic
        or_policy = CompositeAuthorizationPolicy(
            [TruePolicy(), FalsePolicy()],
            strategy=PolicyCompositionStrategy.ANY_MUST_PASS
        )
        self.assertTrue(or_policy.evaluate(identity, "READ"))

    def test_agent_authenticate_task(self) -> None:
        """Verifies agent executes credentials authentication tasks successfully."""
        task = Task(
            description="Authenticate login",
            metadata={
                "action": "authenticate",
                "provider_id": "jwt",
                "credential_type": "password",
                "credential": "correct-secret",
                "workspace": "workspace_1"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertTrue(res.authenticated)

        # Verify success event was published to EventBus
        self.event_bus.dispatch_all()
        events = [e for e in self.receiver.events if e.payload.get("event_name") == "auth.login.success"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["workspace"], "workspace_1")

    def test_agent_authenticate_failure(self) -> None:
        """Verifies agent logs authentication failures and issues events."""
        task = Task(
            description="Authenticate invalid",
            metadata={
                "action": "authenticate",
                "provider_id": "jwt",
                "credential_type": "password",
                "credential": "wrong-secret",
                "workspace": "workspace_1"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertFalse(res.authenticated)

        # Verify failure event was published
        self.event_bus.dispatch_all()
        events = [e for e in self.receiver.events if e.payload.get("event_name") == "auth.login.failed"]
        self.assertEqual(len(events), 1)

    def test_agent_validate_and_evaluate_task(self) -> None:
        """Verifies agent validates tokens and evaluates access policies."""
        # 1. Register a fake session first
        now = datetime.utcnow()
        session = SessionInfo(
            session_id="access-123",
            user_id="user_123",
            created_at=now,
            expires_at=now + timedelta(hours=1),
            last_activity=now,
            device_info="test",
            ip_address="127.0.0.1",
            metadata={"provider_id": "jwt", "workspace": "workspace_1"}
        )
        self.registry._sessions["access-123"] = session

        # 2. Execute validation task
        task_val = Task(
            description="Validate token",
            metadata={
                "action": "validate",
                "token": "access-123",
                "workspace": "workspace_1"
            }
        )
        self.agent.validate_task(task_val)
        self.agent.before_execute(task_val)
        identity = self.agent.execute(task_val)
        self.agent.after_execute(identity)

        self.assertEqual(identity.user_id, "user_123")

        # 3. Execute policy evaluation task
        task_eval = Task(
            description="Evaluate access",
            metadata={
                "action": "evaluate_permission",
                "identity": identity,
                "permission": "READ",
                "resource": "doc_1",
                "context": {"workspace": "workspace_1"}
            }
        )
        self.agent.validate_task(task_eval)
        self.agent.before_execute(task_eval)
        allowed = self.agent.execute(task_eval)
        self.agent.after_execute(allowed)

        self.assertTrue(allowed)

        # 4. Denied evaluation event trigger check
        task_eval_denied = Task(
            description="Evaluate denied access",
            metadata={
                "action": "evaluate_permission",
                "identity": identity,
                "permission": "DELETE",
                "resource": "doc_1",
                "context": {"workspace": "workspace_1"}
            }
        )
        self.agent.validate_task(task_eval_denied)
        self.agent.before_execute(task_eval_denied)
        allowed_denied = self.agent.execute(task_eval_denied)
        self.agent.after_execute(allowed_denied)

        self.assertFalse(allowed_denied)
        self.event_bus.dispatch_all()
        events = [e for e in self.receiver.events if e.payload.get("event_name") == "auth.permission.denied"]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["permission"], "DELETE")

    def test_agent_refresh_and_revoke_task(self) -> None:
        """Verifies token refresh and revocation agent tasks."""
        task_ref = Task(
            description="Refresh token",
            metadata={
                "action": "refresh",
                "provider_id": "jwt",
                "refresh_token": "valid-refresh"
            }
        )
        self.agent.validate_task(task_ref)
        self.agent.before_execute(task_ref)
        res = self.agent.execute(task_ref)
        self.agent.after_execute(res)

        new_access = res.issued_tokens["access_token"]
        self.assertEqual(new_access, "access-new-refreshed")

        # Revoke access token
        task_rev = Task(
            description="Revoke token",
            metadata={
                "action": "revoke",
                "token": new_access
            }
        )
        self.agent.validate_task(task_rev)
        self.agent.before_execute(task_rev)
        success = self.agent.execute(task_rev)
        self.agent.after_execute(success)

        self.assertTrue(success)
        self.assertNotIn(new_access, self.registry._sessions)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            # Register separate dummy providers
            class DummyProvider(AuthenticationProvider):
                def authenticate(self, request): return AuthResponse(False, None)
                def validate_token(self, token, workspace=None): raise AuthValidationError()
                def refresh(self, refresh_token): return AuthResponse(False, None)
                def revoke(self, token): return True
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummyProvider())
            self.assertIn(pid, self.registry.list_providers())

            # Retrieve
            p = self.registry.get_provider(pid)
            self.assertIsNotNone(p)

            # Unregister
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            # Ensure none failed
            for f in futures:
                f.result()
