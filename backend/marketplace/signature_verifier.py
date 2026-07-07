"""Signature verifier ensuring package integrity, checksums, and publisher trust."""

import hashlib
from typing import Dict, Set
from backend.marketplace.models import PackageMetadata


class SignatureVerifier:
    """Validates digital signatures and publisher credentials for marketplace security."""

    def __init__(self) -> None:
        self.trusted_publishers: Set[str] = {"Nexus Core Team", "Google DeepMind", "Official Partner"}
        # Mapping from publisher to public key fingerprint
        self.publisher_keys: Dict[str, str] = {
            "Nexus Core Team": "fp_nexus_official_key_2026",
            "Google DeepMind": "fp_deepmind_key_2026",
            "Official Partner": "fp_partner_key_2026",
        }

    def verify_checksum(self, metadata: PackageMetadata, content_bytes: bytes) -> bool:
        """Verifies if the SHA-256 hash of the content matches the metadata checksum."""
        if not metadata.checksum:
            return False
        content_hash = hashlib.sha256(content_bytes).hexdigest()
        return content_hash == metadata.checksum

    def verify_signature(self, metadata: PackageMetadata, publisher: str) -> bool:
        """Verifies if the package signature is valid and belongs to the specified publisher."""
        if not metadata.digital_signature:
            return False

        # In a production system, this verifies using asymmetric cryptography.
        # We simulate the check by ensuring the signature has a valid structure referencing the publisher key.
        expected_fingerprint = self.publisher_keys.get(publisher)
        if not expected_fingerprint:
            return False

        # Simulate signature payload format: "sig:<package_id>:<version>:<key_fingerprint>"
        parts = metadata.digital_signature.split(":")
        if len(parts) != 4 or parts[0] != "sig":
            return False

        p_id, p_ver, p_fp = parts[1], parts[2], parts[3]
        return p_id == metadata.package_id and p_ver == metadata.version and p_fp == expected_fingerprint

    def is_trusted_publisher(self, publisher: str) -> bool:
        """Checks if the publisher is in the trusted publisher set."""
        return publisher in self.trusted_publishers

    def add_trusted_publisher(self, publisher: str, public_key_fingerprint: str) -> None:
        """Adds a publisher to the trusted set."""
        self.trusted_publishers.add(publisher)
        self.publisher_keys[publisher] = public_key_fingerprint
