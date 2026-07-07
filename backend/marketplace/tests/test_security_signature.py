"""Tests for package signature verifications, checksums, and trust verification."""

import hashlib
import unittest
from backend.marketplace.models import PackageMetadata
from backend.marketplace.signature_verifier import SignatureVerifier


class TestSecuritySignature(unittest.TestCase):
    """Verifies the SignatureVerifier behavior with valid and invalid parameters."""

    def setUp(self) -> None:
        self.verifier = SignatureVerifier()

    def test_checksum_validation(self) -> None:
        """Tests that verifier matches content bytes against SHA-256 hashes."""
        content = b"package-data-bytes"
        expected_hash = hashlib.sha256(content).hexdigest()

        meta = PackageMetadata(
            package_id="test_pkg",
            version="1.0.0",
            author="Google DeepMind",
            license="MIT",
            description="A test package",
            checksum=expected_hash
        )

        self.assertTrue(self.verifier.verify_checksum(meta, content))
        self.assertFalse(self.verifier.verify_checksum(meta, b"tampered-content"))

    def test_signature_validation(self) -> None:
        """Tests simulated asymmetric signature checks."""
        # Signature format: "sig:<package_id>:<version>:<key_fingerprint>"
        meta = PackageMetadata(
            package_id="nlp_agent",
            version="2.1.0",
            author="Google DeepMind",
            license="Apache-2.0",
            description="Agent",
            digital_signature="sig:nlp_agent:2.1.0:fp_deepmind_key_2026"
        )

        self.assertTrue(self.verifier.verify_signature(meta, "Google DeepMind"))
        self.assertFalse(self.verifier.verify_signature(meta, "Malicious Author"))

        # Bad signature structure
        meta.digital_signature = "invalid_format_string"
        self.assertFalse(self.verifier.verify_signature(meta, "Google DeepMind"))

    def test_publisher_trust(self) -> None:
        """Tests trusted publisher verification and manual registration."""
        self.assertTrue(self.verifier.is_trusted_publisher("Nexus Core Team"))
        self.assertFalse(self.verifier.is_trusted_publisher("Unknown Publisher"))

        self.verifier.add_trusted_publisher("New Publisher", "fp_new_key")
        self.assertTrue(self.verifier.is_trusted_publisher("New Publisher"))
