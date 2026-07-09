"""Checksum generator calculating SHA256 hashes of release binaries."""

from __future__ import annotations

import hashlib


class ChecksumGenerator:
    """Calculates cryptographic verification hashes."""

    @staticmethod
    def calculate_sha256(data: bytes) -> str:
        """Computes the SHA256 hex digest of a byte sequence.

        Args:
            data: Binary payload.

        Returns:
            The hex digest string.
        """
        hasher = hashlib.sha256()
        hasher.update(data)
        return hasher.hexdigest()
DefinitionPath = "checksum_generator.py"
