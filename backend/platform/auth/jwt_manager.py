"""JWT Manager module using standard libraries for token encoding and decoding."""

import base64
import hmac
import hashlib
import json
import time
from typing import Any, Dict, Optional


class JWTManager:
    """Manages creation, parsing, and signature verification of JWT tokens."""

    def __init__(self, secret_key: str, algorithm: str = "HS256", default_expiry_seconds: int = 3600) -> None:
        """Initializes the JWT Manager.

        Args:
            secret_key: Symmetric key used for signing.
            algorithm: Only HS256 is supported by default.
            default_expiry_seconds: Standard token life if not specified.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.default_expiry = default_expiry_seconds

    def _base64url_encode(self, data: bytes) -> str:
        """Encodes bytes into base64url string."""
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def _base64url_decode(self, data: str) -> bytes:
        """Decodes base64url string into bytes."""
        padding = "=" * (4 - (len(data) % 4))
        return base64.urlsafe_b64decode(data + padding)

    def encode(self, payload: Dict[str, Any]) -> str:
        """Creates a signed JWT token.

        Args:
            payload: Claims to embed.

        Returns:
            The signed JWT token as a string.
        """
        header = {"alg": self.algorithm, "typ": "JWT"}
        
        # Ensure exp claim is set if not present
        if "exp" not in payload:
            payload["exp"] = int(time.time()) + self.default_expiry

        header_b64 = self._base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = self._base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        
        # Sign with HMAC-SHA256
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()
        
        signature_b64 = self._base64url_encode(signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def decode(self, token: str) -> Dict[str, Any]:
        """Decodes and validates a signed JWT token.

        Args:
            token: The JWT token string.

        Returns:
            The decoded payload dict.

        Raises:
            ValueError: If signature is invalid, token is expired, or format is wrong.
        """
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token format")

        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(
            self.secret_key.encode("utf-8"),
            signing_input,
            hashlib.sha256
        ).digest()
        
        if not hmac.compare_digest(self._base64url_decode(signature_b64), expected_sig):
            raise ValueError("Signature verification failed")

        payload_bytes = self._base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp and int(time.time()) > exp:
            raise ValueError("Token has expired")

        return payload
