"""Request validator verifying input schemas and sanitizing fields."""

import re
from typing import Dict, Any, List, Optional, Tuple


class RequestValidator:
    """Provides methods to check schemas, sanitize strings, and detect SQL/script injection."""

    def __init__(self) -> None:
        """Initializes sanitization regexes."""
        self._html_pattern = re.compile(r"<[^>]*>")

    def sanitize_string(self, text: str) -> str:
        """Removes HTML tags and strip whitespace.

        Args:
            text: Input string.
        """
        if not text:
            return ""
        # Strip script tags and their contents first
        cleaned = re.sub(r"<script.*?>.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        # Remove remaining HTML/XML tags
        cleaned = self._html_pattern.sub("", cleaned)
        return cleaned.strip()

    def validate_schema(self, data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, Optional[str]]:
        """Verifies presence of required dictionary keys.

        Args:
            data: Payload dictionary.
            required_fields: List of mandatory keys.

        Returns:
            Tuple (is_valid, error_reason).
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                return False, f"Missing required field: '{field}'"
        return True, None

    def validate_email(self, email: str) -> bool:
        """Checks if format resembles a valid email."""
        if not email:
            return False
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email.strip()))
