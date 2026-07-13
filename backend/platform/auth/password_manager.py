"""Password manager module for hashing and verifying passwords securely."""

import hashlib
import os
import secrets
from typing import Tuple


class PasswordManager:
    """Provides methods to hash and verify passwords using PBKDF2-HMAC-SHA256."""

    def __init__(self, iterations: int = 100000, salt_length: int = 16) -> None:
        """Initializes the password manager.

        Args:
            iterations: Number of PBKDF2 iterations.
            salt_length: Salt length in bytes.
        """
        self.iterations = iterations
        self.salt_length = salt_length

    def hash_password(self, password: str) -> str:
        """Hashes a password with a randomly generated salt.

        Args:
            password: The plaintext password.

        Returns:
            A string containing iterations, salt (hex), and hash (hex) separated by '$'.
        """
        salt = secrets.token_bytes(self.salt_length)
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, self.iterations
        )
        return f"{self.iterations}${salt.hex()}${key.hex()}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifies a password against a hash.

        Args:
            password: The plaintext password to verify.
            hashed_password: The stored hashed password string.

        Returns:
            True if the password matches, False otherwise.
        """
        try:
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False
            iterations = int(parts[0])
            salt = bytes.fromhex(parts[1])
            original_key = bytes.fromhex(parts[2])

            new_key = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations
            )
            return secrets.compare_digest(original_key, new_key)
        except Exception:
            return False
