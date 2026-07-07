"""Credential Manager handling encrypted credential storage and token refresh cycles."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional


class CredentialManager:
    """Manages secure encryption/decryption wrapper for API keys and tokens."""

    def __init__(self, key: str = "nexus-operation-secret-key") -> None:
        self._key = key

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypts credentials to base64 string."""
        serialized = json.dumps(credentials)
        encoded = base64.b64encode(serialized.encode("utf-8"))
        return encoded.decode("utf-8")

    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, Any]:
        """Decrypts base64 string back to dictionary credentials."""
        decoded = base64.b64decode(encrypted_str.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))

    def refresh_oauth_token(self, auth_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates OAuth token refresh exchange loops."""
        if "refresh_token" in auth_data:
            auth_data["access_token"] = f"refreshed-token-{base64.b64encode(auth_data['refresh_token'].encode()).hex()[:8]}"
        return auth_data
