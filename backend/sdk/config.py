"""SDK configuration for Nexus AI public API clients."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

from backend.sdk.version import API_VERSION, validate_api_version


@dataclass
class NexusConfig:
    """Configuration for Nexus AI SDK clients.

    Attributes:
        base_url: Base URL of the Nexus AI API server.
        api_key: Optional API key for ``X-API-Key`` authentication.
        bearer_token: Optional bearer token for ``Authorization`` header.
        api_version: API version prefix (default ``v1``).
        timeout: Default request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.
        workspace_id: Default workspace identifier for requests.
        user_agent: HTTP User-Agent header value.
        extra_headers: Additional headers merged into every request.
    """

    base_url: str = "http://127.0.0.1:8000"
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None
    api_version: str = API_VERSION
    timeout: float = 60.0
    max_retries: int = 3
    workspace_id: str = "default-ws"
    user_agent: str = f"NexusAI-Python-SDK/{API_VERSION}"
    extra_headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        validate_api_version(self.api_version)
        self.base_url = self.base_url.rstrip("/")

    @classmethod
    def from_env(cls) -> NexusConfig:
        """Builds configuration from environment variables.

        Environment variables:
            NEXUS_API_URL: Base API URL.
            NEXUS_API_KEY: API key.
            NEXUS_BEARER_TOKEN: Bearer token.
            NEXUS_API_VERSION: API version prefix.
            NEXUS_WORKSPACE_ID: Default workspace ID.
            NEXUS_TIMEOUT: Request timeout in seconds.

        Returns:
            NexusConfig: Populated configuration instance.
        """
        return cls(
            base_url=os.getenv("NEXUS_API_URL", "http://127.0.0.1:8000"),
            api_key=os.getenv("NEXUS_API_KEY"),
            bearer_token=os.getenv("NEXUS_BEARER_TOKEN"),
            api_version=os.getenv("NEXUS_API_VERSION", API_VERSION),
            timeout=float(os.getenv("NEXUS_TIMEOUT", "60")),
            workspace_id=os.getenv("NEXUS_WORKSPACE_ID", "default-ws"),
        )

    @property
    def api_base(self) -> str:
        """Returns the fully qualified API base path.

        Returns:
            URL prefix including API version (e.g. ``http://host/v1``).
        """
        return f"{self.base_url}/{self.api_version}"
