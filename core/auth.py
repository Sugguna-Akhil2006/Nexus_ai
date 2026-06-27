"""Authentication and Authorization Module for Nexus Agent Framework.

This module provides provider-independent authentication and authorization
services including identity verification, session management, permission
evaluation (RBAC), and policy composition.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import re
import threading
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from core.base import AgentState, AgentStatus, BaseAgent
from core.event import Event, EventBus, EventType
from core.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from core.task import Task
from core.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class AuthError(NexusException):
    """Base exception for all Authentication and Authorization errors."""
    pass


class AuthValidationError(AuthError):
    """Raised when authentication credentials or formats are invalid."""
    pass


class AuthorizationError(AuthError):
    """Raised when authorization checks or permission checks fail."""
    pass


class SessionExpiredError(AuthError):
    """Raised when a session or token has expired."""
    pass


# =====================================================================
# Enums and Data Models
# =====================================================================

class Permission(Enum):
    """Supported authorization permission types."""
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    ADMIN = "ADMIN"
    BILLING = "BILLING"
    ANALYTICS = "ANALYTICS"
    WORKSPACE_MANAGE = "WORKSPACE_MANAGE"
    AGENT_EXECUTE = "AGENT_EXECUTE"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True)
class UserIdentity:
    """Immutable model representing resolved user identity information.

    Attributes:
        user_id: Unique identifier for the user.
        username: Unique username.
        email: Primary contact email.
        display_name: Printable display name.
        tenant_id: Target tenant or workspace organization context.
        roles: List of roles assigned to the user.
        permissions: List of permission strings explicitly assigned.
        status: Account status (e.g. "active", "suspended").
        metadata: Custom metadata dictionary.
    """
    user_id: str
    username: str
    email: str
    display_name: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthRequest:
    """Authentication request containing credentials for verification.

    Attributes:
        request_id: Tracking request ID.
        credential_type: Category of credential (e.g. "token", "api_key", "password").
        credential: Secret value of the credential.
        workspace: Targeted tenant workspace/tenant.
        metadata: Extra options mapping.
    """
    request_id: str
    credential_type: str
    credential: str
    workspace: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AuthResponse:
    """Result outcome of authentication requests.

    Attributes:
        authenticated: True if identity is successfully verified.
        identity: Resolved UserIdentity on success, None on failure.
        issued_tokens: Dictionary of issued tokens (e.g. access/refresh tokens).
        expiration: Datetime indicating token expiration.
        audit_id: Unique identifier tracing this login event.
        metadata: Extra contextual response metadata.
    """
    authenticated: bool
    identity: Optional[UserIdentity]
    issued_tokens: Dict[str, str] = field(default_factory=dict)
    expiration: Optional[datetime] = None
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionInfo:
    """Active session parameters stored in memory.

    Attributes:
        session_id: Unique identifier of the session.
        user_id: Identifier of the associated user.
        created_at: Datetime indicating session creation.
        expires_at: Datetime indicating session expiration.
        last_activity: Datetime indicating last activity recorded.
        device_info: Hardware or agent context details.
        ip_address: Source network IP.
        metadata: Custom metadata.
    """
    session_id: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    last_activity: datetime
    device_info: str
    ip_address: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Checks if session has expired based on current UTC time."""
        return datetime.utcnow() > self.expires_at


# =====================================================================
# Validation Utilities
# =====================================================================

def validate_username(username: str) -> None:
    """Validates username syntax rules.

    Args:
        username: The username to check.

    Raises:
        AuthValidationError: If validation fails.
    """
    if not username or not isinstance(username, str) or len(username.strip()) < 3:
        raise AuthValidationError("Username must be a non-empty string of at least 3 characters.")
    if not re.match(r"^[a-zA-Z0-9_\-\.@]+$", username):
        raise AuthValidationError("Username can only contain alphanumeric characters, underscores, hyphens, dots, and @.")


def validate_email(email: str) -> None:
    """Validates email format rules.

    Args:
        email: The email address to check.

    Raises:
        AuthValidationError: If validation fails.
    """
    if not email or not isinstance(email, str):
        raise AuthValidationError("Email must be a valid non-empty string.")
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        raise AuthValidationError("Invalid email address format.")


def validate_role(role: str) -> None:
    """Validates role naming syntax.

    Args:
        role: The role name to check.

    Raises:
        AuthValidationError: If validation fails.
    """
    if not role or not isinstance(role, str) or not role.strip():
        raise AuthValidationError("Role name cannot be empty.")


def validate_permission(permission: Union[str, Permission]) -> None:
    """Validates permission enum or name value.

    Args:
        permission: The permission to check.

    Raises:
        AuthValidationError: If validation fails.
    """
    if not permission:
        raise AuthValidationError("Permission cannot be empty.")
    if isinstance(permission, Permission):
        return
    perm_str = str(permission).upper()
    valid_perms = {p.value for p in Permission}
    if perm_str not in valid_perms and not str(permission).strip():
        raise AuthValidationError(f"Invalid permission value: {permission}")


# =====================================================================
# Provider Abstraction
# =====================================================================

class AuthenticationProvider(ABC):
    """Abstract Base Class defining the contract for identity providers."""

    @abstractmethod
    def authenticate(self, request: AuthRequest) -> AuthResponse:
        """Authenticate user credentials.

        Args:
            request: AuthRequest payload.

        Returns:
            AuthResponse: Verification details and tokens.

        Raises:
            AuthValidationError: If credentials are invalid.
        """
        pass

    @abstractmethod
    def validate_token(self, token: str, workspace: Optional[str] = None) -> UserIdentity:
        """Validate token and resolve identity.

        Args:
            token: The access token.
            workspace: The optional tenant workspace.

        Returns:
            UserIdentity: Resolved identity.

        Raises:
            SessionExpiredError: If token has expired.
            AuthValidationError: If token is invalid.
        """
        pass

    @abstractmethod
    def refresh(self, refresh_token: str) -> AuthResponse:
        """Issues new tokens using refresh token.

        Args:
            refresh_token: The refresh token.

        Returns:
            AuthResponse: New token payload.

        Raises:
            SessionExpiredError: If refresh token has expired.
            AuthValidationError: If refresh token is invalid.
        """
        pass

    @abstractmethod
    def revoke(self, token: str) -> bool:
        """Revokes a token.

        Args:
            token: The token to invalidate.

        Returns:
            bool: True if token was successfully revoked.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks provider connection state.

        Returns:
            bool: True if service is healthy.
        """
        pass


# =====================================================================
# Registry
# =====================================================================

class AuthenticationRegistry:
    """Thread-safe registry for identity providers and active sessions."""

    _instance: Optional["AuthenticationRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "AuthenticationRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._providers: Dict[str, AuthenticationProvider] = {}
            self._sessions: Dict[str, SessionInfo] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: AuthenticationProvider) -> None:
        """Registers an AuthenticationProvider.

        Args:
            provider_id: Unique provider ID.
            provider: Concrete provider instance.

        Raises:
            AuthValidationError: On duplicate IDs or invalid configurations.
        """
        if not provider_id or not str(provider_id).strip():
            raise AuthValidationError("provider_id cannot be empty.")
        if not provider:
            raise AuthValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise AuthValidationError(f"Provider '{provider_id}' is already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"Registered auth provider: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes a registered provider.

        Args:
            provider_id: Unique provider ID.

        Raises:
            AuthValidationError: If provider is not registered.
        """
        with self._lock:
            if provider_id not in self._providers:
                raise AuthValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"Unregistered auth provider: {provider_id}")

    def authenticate(self, provider_id: str, request: AuthRequest) -> AuthResponse:
        """Authenticates request through target provider and creates session.

        Args:
            provider_id: Unique provider ID.
            request: The credentials request.

        Returns:
            AuthResponse: Combined outcome.
        """
        provider = self.get_provider(provider_id)
        response = provider.authenticate(request)

        if response.authenticated and response.identity:
            access_token = response.issued_tokens.get("access_token") or str(uuid.uuid4())
            expires_in = 3600
            if response.expiration:
                expires_in = int((response.expiration - datetime.utcnow()).total_seconds())
                if expires_in <= 0:
                    expires_in = 3600

            device_info = request.metadata.get("device_info", "unknown")
            ip_address = request.metadata.get("ip_address", "127.0.0.1")

            now = datetime.utcnow()
            session = SessionInfo(
                session_id=access_token,
                user_id=response.identity.user_id,
                created_at=now,
                expires_at=now + timedelta(seconds=expires_in),
                last_activity=now,
                device_info=device_info,
                ip_address=ip_address,
                metadata={
                    "provider_id": provider_id,
                    "workspace": request.workspace
                }
            )

            with self._lock:
                self._sessions[access_token] = session
                self._logger.info(f"Session established for user: {response.identity.user_id}")

        return response

    def validate(self, token: str, workspace: Optional[str] = None) -> UserIdentity:
        """Validates token checking sessions and provider resolution.

        Args:
            token: Access token.
            workspace: Target workspace for isolation validation.

        Returns:
            UserIdentity: Resolved user profile.
        """
        with self._lock:
            if token in self._sessions:
                session = self._sessions[token]
                if session.is_expired():
                    del self._sessions[token]
                    raise SessionExpiredError("Session has expired.")

                session.last_activity = datetime.utcnow()
                session_workspace = session.metadata.get("workspace")
                if workspace and session_workspace != workspace:
                    raise AuthorizationError(
                        f"Workspace mismatch. Session workspace: '{session_workspace}', "
                        f"Requested workspace: '{workspace}'"
                    )

                provider_id = session.metadata.get("provider_id")
                if provider_id:
                    provider = self.get_provider(provider_id)
                    return provider.validate_token(token, workspace)

            # Try validating on all providers
            for pid, provider in self._providers.items():
                try:
                    identity = provider.validate_token(token, workspace)
                    # Cache successful sessions in memory
                    now = datetime.utcnow()
                    session = SessionInfo(
                        session_id=token,
                        user_id=identity.user_id,
                        created_at=now,
                        expires_at=now + timedelta(seconds=3600),
                        last_activity=now,
                        device_info="inferred",
                        ip_address="127.0.0.1",
                        metadata={
                            "provider_id": pid,
                            "workspace": workspace or identity.tenant_id
                        }
                    )
                    self._sessions[token] = session
                    return identity
                except (AuthValidationError, SessionExpiredError):
                    continue

            raise AuthValidationError("Invalid or unrecognized token.")

    def refresh(self, provider_id: str, refresh_token: str) -> AuthResponse:
        """Refreshes tokens and updates cached session context."""
        provider = self.get_provider(provider_id)
        response = provider.refresh(refresh_token)

        if response.authenticated and response.identity:
            with self._lock:
                if refresh_token in self._sessions:
                    del self._sessions[refresh_token]

                access_token = response.issued_tokens.get("access_token") or str(uuid.uuid4())
                expires_in = 3600
                if response.expiration:
                    expires_in = int((response.expiration - datetime.utcnow()).total_seconds())
                    if expires_in <= 0:
                        expires_in = 3600

                now = datetime.utcnow()
                session = SessionInfo(
                    session_id=access_token,
                    user_id=response.identity.user_id,
                    created_at=now,
                    expires_at=now + timedelta(seconds=expires_in),
                    last_activity=now,
                    device_info="refreshed",
                    ip_address="127.0.0.1",
                    metadata={
                        "provider_id": provider_id,
                        "workspace": response.identity.tenant_id
                    }
                )
                self._sessions[access_token] = session

        return response

    def revoke(self, token: str) -> bool:
        """Revokes a session and informs its provider."""
        with self._lock:
            revoked = False
            if token in self._sessions:
                session = self._sessions[token]
                provider_id = session.metadata.get("provider_id")
                if provider_id and provider_id in self._providers:
                    try:
                        self._providers[provider_id].revoke(token)
                    except Exception:
                        pass
                del self._sessions[token]
                revoked = True

            for provider in self._providers.values():
                try:
                    if provider.revoke(token):
                        revoked = True
                except Exception:
                    pass

            return revoked

    def get_provider(self, provider_id: str) -> AuthenticationProvider:
        """Retrieves registered provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise AuthValidationError(f"Provider '{provider_id}' is not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists active provider IDs."""
        with self._lock:
            return list(self._providers.keys())

    def health_check(self) -> Dict[str, bool]:
        """Performs health check on registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# Authorization Engine
# =====================================================================

class AuthorizationPolicy(ABC):
    """Abstract Base Class representing an evaluation policy rule."""

    @abstractmethod
    def evaluate(
        self,
        identity: UserIdentity,
        permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Evaluates access request permission against the identity.

        Args:
            identity: Subject identity details.
            permission: Action permission name requested.
            resource: Resource identifier target.
            context: Additional custom contextual payload attributes (ABAC).

        Returns:
            bool: True if access is permitted, False otherwise.
        """
        pass


class DefaultAuthorizationPolicy(AuthorizationPolicy):
    """Policy supporting Role-Based Access Control and Tenant Isolation."""

    DEFAULT_ROLE_PERMISSIONS: Dict[str, Set[str]] = {
        "admin": {p.value for p in Permission} | {"READ", "WRITE", "DELETE", "ADMIN", "BILLING", "ANALYTICS", "WORKSPACE_MANAGE", "AGENT_EXECUTE", "SYSTEM"},
        "developer": {"READ", "WRITE", "ANALYTICS", "AGENT_EXECUTE"},
        "viewer": {"READ", "ANALYTICS"},
        "user": {"READ", "WRITE", "AGENT_EXECUTE"},
    }

    def __init__(self, role_permissions: Optional[Dict[str, Set[str]]] = None) -> None:
        self.role_permissions = role_permissions or self.DEFAULT_ROLE_PERMISSIONS

    def evaluate(
        self,
        identity: UserIdentity,
        permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not identity:
            return False

        ctx = context or {}

        # Tenant Isolation check
        req_workspace = ctx.get("tenant_id") or ctx.get("workspace")
        if req_workspace and identity.tenant_id != req_workspace:
            return False

        # Normalize permission
        perm_str = str(permission).upper()

        # Check explicit permissions list
        user_perms = {p.upper() if isinstance(p, str) else p.value.upper() for p in identity.permissions}
        if "ADMIN" in user_perms or perm_str in user_perms:
            return True

        # Check permissions mapped to user roles
        for role in identity.roles:
            role_norm = str(role).lower()
            if role_norm in self.role_permissions:
                mapped_perms = self.role_permissions[role_norm]
                if "ADMIN" in mapped_perms or perm_str in mapped_perms:
                    return True

        return False


class PolicyCompositionStrategy(Enum):
    """Policy grouping evaluation strategies."""
    ALL_MUST_PASS = "ALL_MUST_PASS"
    ANY_MUST_PASS = "ANY_MUST_PASS"


class CompositeAuthorizationPolicy(AuthorizationPolicy):
    """Combines multiple policies using composite evaluation strategies."""

    def __init__(
        self,
        policies: List[AuthorizationPolicy],
        strategy: PolicyCompositionStrategy = PolicyCompositionStrategy.ALL_MUST_PASS
    ) -> None:
        self.policies = policies
        self.strategy = strategy

    def evaluate(
        self,
        identity: UserIdentity,
        permission: str,
        resource: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        if not self.policies:
            return True

        if self.strategy == PolicyCompositionStrategy.ALL_MUST_PASS:
            return all(p.evaluate(identity, permission, resource, context) for p in self.policies)
        else:
            return any(p.evaluate(identity, permission, resource, context) for p in self.policies)


# =====================================================================
# Authentication Agent
# =====================================================================

class AuthenticationAgent(BaseAgent):
    """System agent providing identity verification and authorization checks."""

    def __init__(
        self,
        name: str = "AuthenticationAgent",
        description: str = "Handles identity, token verification, session lifecycle, and permission evaluation",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["AUTHENTICATION", "AUTHORIZATION"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = AuthenticationRegistry()
        self.policy: AuthorizationPolicy = DefaultAuthorizationPolicy()
        self.event_bus = EventBus()

    def initialize(self) -> None:
        """Initializes the agent."""
        super().initialize()

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]

        if action == "authenticate":
            provider_id = task.metadata.get("provider_id")
            credential_type = task.metadata.get("credential_type")
            credential = task.metadata.get("credential")
            workspace = task.metadata.get("workspace")
            req_metadata = task.metadata.get("metadata", {})

            if not credential_type or not credential or not workspace:
                raise AuthValidationError("Missing credential_type, credential, or workspace in task metadata.")

            if not provider_id:
                providers = self.registry.list_providers()
                if not providers:
                    raise AuthValidationError("No authentication providers registered.")
                provider_id = providers[0]

            req = AuthRequest(
                request_id=str(uuid.uuid4()),
                credential_type=credential_type,
                credential=credential,
                workspace=workspace,
                metadata=req_metadata
            )

            try:
                response = self.registry.authenticate(provider_id, req)
                if response.authenticated:
                    user_id = response.identity.user_id if response.identity else None
                    self._publish_event("auth.login.success", user_id=user_id, workspace=workspace)
                else:
                    self._publish_event("auth.login.failed", workspace=workspace, reason="Invalid credentials")
                return response
            except Exception as e:
                self._publish_event("auth.login.failed", workspace=workspace, reason=str(e))
                raise

        elif action == "validate":
            token = task.metadata.get("token")
            workspace = task.metadata.get("workspace")

            if not token:
                raise AuthValidationError("Missing 'token' in validation task metadata.")

            try:
                identity = self.registry.validate(token, workspace)
                return identity
            except SessionExpiredError as e:
                self._publish_event("auth.session.expired", token=token, reason=str(e))
                raise
            except Exception:
                raise

        elif action == "evaluate_permission":
            identity_data = task.metadata.get("identity")
            permission = task.metadata.get("permission")
            resource = task.metadata.get("resource")
            context = task.metadata.get("context", {})

            if not identity_data or not permission:
                raise AuthValidationError("Missing 'identity' or 'permission' in policy evaluation task.")

            # Reconstruct UserIdentity if passed as dict
            if isinstance(identity_data, dict):
                identity = UserIdentity(
                    user_id=identity_data["user_id"],
                    username=identity_data["username"],
                    email=identity_data["email"],
                    display_name=identity_data["display_name"],
                    tenant_id=identity_data["tenant_id"],
                    roles=identity_data["roles"],
                    permissions=identity_data["permissions"],
                    status=identity_data["status"],
                    metadata=identity_data.get("metadata", {})
                )
            else:
                identity = identity_data

            allowed = self.policy.evaluate(identity, permission, resource, context)
            if not allowed:
                self._publish_event(
                    "auth.permission.denied",
                    user_id=identity.user_id,
                    permission=permission,
                    resource=resource
                )
            return allowed

        elif action == "refresh":
            provider_id = task.metadata.get("provider_id")
            refresh_token = task.metadata.get("refresh_token")

            if not refresh_token:
                raise AuthValidationError("Missing 'refresh_token' in refresh task metadata.")

            if not provider_id:
                providers = self.registry.list_providers()
                if not providers:
                    raise AuthValidationError("No authentication providers registered.")
                provider_id = providers[0]

            try:
                response = self.registry.refresh(provider_id, refresh_token)
                if response.authenticated:
                    self._publish_event(
                        "auth.token.refreshed",
                        user_id=response.identity.user_id if response.identity else None
                    )
                return response
            except SessionExpiredError as e:
                self._publish_event("auth.session.expired", token=refresh_token, reason=str(e))
                raise
            except Exception:
                raise

        elif action == "revoke":
            token = task.metadata.get("token")
            if not token:
                raise AuthValidationError("Missing 'token' in revocation task metadata.")

            success = self.registry.revoke(token)
            if success:
                self._publish_event("auth.logout", token=token)
            return success

        else:
            raise AuthValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="AuthenticationAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
