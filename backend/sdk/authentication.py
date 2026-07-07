"""Authentication helpers for Nexus AI SDK clients."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from backend.sdk.config import NexusConfig
from backend.sdk.exceptions import AuthenticationError


@dataclass
class AuthCredentials:
    """Resolved authentication credentials for API requests.

    Attributes:
        api_key: Value for the ``X-API-Key`` header.
        bearer_token: Value for the ``Authorization: Bearer`` header.
    """

    api_key: Optional[str] = None
    bearer_token: Optional[str] = None

    def is_authenticated(self) -> bool:
        """Returns whether any credential is present.

        Returns:
            True when an API key or bearer token is configured.
        """
        return bool(self.api_key or self.bearer_token)

    def to_headers(self) -> Dict[str, str]:
        """Builds authentication HTTP headers.

        Returns:
            Header dictionary with credential headers when present.

        Raises:
            AuthenticationError: When no credentials are configured.
        """
        if not self.is_authenticated():
            raise AuthenticationError(
                "No authentication credentials configured. "
                "Set api_key or bearer_token on NexusConfig."
            )
        headers: Dict[str, str] = {}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers


class Authenticator:
    """Manages SDK authentication state and header injection."""

    def __init__(self, config: NexusConfig) -> None:
        self._config = config
        self._credentials = AuthCredentials(
            api_key=config.api_key,
            bearer_token=config.bearer_token,
        )

    @property
    def credentials(self) -> AuthCredentials:
        """Returns the current authentication credentials.

        Returns:
            AuthCredentials instance.
        """
        return self._credentials

    def set_api_key(self, api_key: str) -> None:
        """Updates the API key credential.

        Args:
            api_key: New API key value.
        """
        self._credentials = AuthCredentials(
            api_key=api_key,
            bearer_token=self._credentials.bearer_token,
        )
        self._config.api_key = api_key

    def set_bearer_token(self, token: str) -> None:
        """Updates the bearer token credential.

        Args:
            token: New bearer token value.
        """
        self._credentials = AuthCredentials(
            api_key=self._credentials.api_key,
            bearer_token=token,
        )
        self._config.bearer_token = token

    def build_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Builds complete request headers including authentication.

        Args:
            extra: Optional additional headers to merge.

        Returns:
            Complete header dictionary for an HTTP request.
        """
        headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self._config.user_agent,
        }
        headers.update(self._config.extra_headers)
        if extra:
            headers.update(extra)
        try:
            headers.update(self._credentials.to_headers())
        except AuthenticationError:
            pass
        return headers
