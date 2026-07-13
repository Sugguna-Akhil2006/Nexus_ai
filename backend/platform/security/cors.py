"""Cross-Origin Resource Sharing (CORS) manager validating origins."""

from typing import List, Dict, Optional


class CORSManager:
    """Evaluates cross-origin requests and formats HTTP CORS headers."""

    def __init__(
        self,
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        allow_credentials: bool = True
    ) -> None:
        """Initializes settings.

        Args:
            allowed_origins: List of permitted origins (wildcard '*' supported).
            allowed_methods: Permitted request methods.
            allowed_headers: Permitted request headers.
            allow_credentials: Allow cookie credentials.
        """
        self.origins = allowed_origins or ["*"]
        self.methods = allowed_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
        self.headers = allowed_headers or ["Content-Type", "Authorization", "X-CSRF-Token"]
        self.allow_credentials = allow_credentials

    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Evaluates if an origin meets CORS whitelist policies."""
        if not origin:
            return False
        if "*" in self.origins:
            return True
        return origin in self.origins

    def get_cors_headers(self, origin: Optional[str]) -> Dict[str, str]:
        """Builds standard headers for preflight or active responses."""
        headers = {}
        if self.is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin or "*"
            headers["Access-Control-Allow-Methods"] = ", ".join(self.methods)
            headers["Access-Control-Allow-Headers"] = ", ".join(self.headers)
            if self.allow_credentials:
                headers["Access-Control-Allow-Credentials"] = "true"
        return headers
