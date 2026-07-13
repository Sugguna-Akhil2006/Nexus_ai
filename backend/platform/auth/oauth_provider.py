"""OAuth provider interface and templates for third-party authentication."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import urllib.parse


class OAuthProvider(ABC):
    """Abstract Base Class for OAuth2 identity providers."""

    def __init__(self, provider_name: str, client_id: str, client_secret: str, redirect_uri: str) -> None:
        """Initializes the OAuth provider settings.

        Args:
            provider_name: E.g., 'github' or 'google'.
            client_id: Registered OAuth client identifier.
            client_secret: Registered client secret credential.
            redirect_uri: Callback URI configured with provider.
        """
        self.provider_name = provider_name
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    @abstractmethod
    def get_authorization_url(self, state: str) -> str:
        """Constructs the provider redirect authorization URL.

        Args:
            state: CSRF state protection token.
        """
        pass

    @abstractmethod
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access token.

        Args:
            code: The OAuth authorization code.
        """
        pass

    @abstractmethod
    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Fetches the user details from the resource server using access token.

        Args:
            access_token: Token fetched from exchange.
        """
        pass


class GitHubOAuthProvider(OAuthProvider):
    """GitHub implementation of the OAuth2 protocol flow."""

    def get_authorization_url(self, state: str) -> str:
        """Constructs the GitHub login page redirect URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "state": state,
            "scope": "read:user user:email"
        }
        return f"https://github.com/login/oauth/authorize?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Simulates/implements the token exchange API request."""
        # Typically makes an HTTP request to https://github.com/login/oauth/access_token
        # Returning mock token details in placeholder configuration for clean runtime.
        return {
            "access_token": f"github_access_token_{code}",
            "token_type": "bearer",
            "scope": "read:user user:email"
        }

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        """Simulates/implements the user profile API call."""
        # Typically fetches GET https://api.github.com/user
        return {
            "id": 1234567,
            "login": "oauth_github_user",
            "email": "github_user@example.com",
            "name": "GitHub OAuth User"
        }
