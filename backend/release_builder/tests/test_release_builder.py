"""Unit and E2E integration tests for the Release Candidate Builder."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.release_builder.artifact_packager import ArtifactPackager
from backend.release_builder.changelog_generator import ChangelogGenerator
from backend.release_builder.checksum_generator import ChecksumGenerator
from backend.release_builder.dependency_auditor import DependencyAuditor
from backend.release_builder.distribution_manager import DistributionManager
from backend.release_builder.license_checker import LicenseChecker
from backend.release_builder.manifest_generator import ManifestGenerator
from backend.release_builder.models import ReleaseType
from backend.release_builder.release_builder import ReleaseCandidateBuilder
from backend.release_builder.release_notes import ReleaseNotesCompiler
from backend.release_builder.version_manager import VersionManager


class TestVersionManager(unittest.TestCase):
    """Verifies semantic version parsing and increments."""

    def test_parse_semver(self) -> None:
        v = VersionManager.parse_version("1.2.3-rc.4+build.12")
        self.assertIsNotNone(v)
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertEqual(v.pre_release, "rc.4")
        self.assertEqual(v.build_metadata, "build.12")

    def test_increment_rc(self) -> None:
        next_ver = VersionManager.increment_version("1.0.0-rc.1", ReleaseType.RC)
        self.assertEqual(next_ver, "1.0.0-rc.2")

    def test_stable_release(self) -> None:
        next_ver = VersionManager.increment_version("1.0.0-rc.3", ReleaseType.STABLE)
        self.assertEqual(next_ver, "1.0.0")

    def test_hotfix_release(self) -> None:
        next_ver = VersionManager.increment_version("1.0.0", ReleaseType.HOTFIX)
        self.assertEqual(next_ver, "1.0.1")

    def test_nightly_release(self) -> None:
        next_ver = VersionManager.increment_version("1.0.0", ReleaseType.NIGHTLY)
        self.assertIn("nightly", next_ver)


class TestArtifactPackager(unittest.TestCase):
    """Verifies packaging in-memory ZIP distributions."""

    def test_package_bundle(self) -> None:
        art = ArtifactPackager.package_bundle(
            name="test-src.zip",
            artifact_type="source",
            files={"hello.py": "print('hello')"},
        )
        self.assertEqual(art.name, "test-src.zip")
        self.assertEqual(art.artifact_type, "source")
        self.assertGreater(art.size_bytes, 0)
        self.assertTrue(len(art.sha256) > 0)


class TestChecksumGenerator(unittest.TestCase):
    """Verifies SHA256 hashes calculations."""

    def test_sha256(self) -> None:
        digest = ChecksumGenerator.calculate_sha256(b"hello world")
        self.assertEqual(digest, "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")


class TestManifestGenerator(unittest.TestCase):
    """Verifies build metadata manifest compiles."""

    def test_manifest(self) -> None:
        manifest = ManifestGenerator.generate_manifest("1.0.0", ["req"], ["openai"])
        self.assertEqual(manifest.version, "1.0.0")
        self.assertEqual(manifest.git_commit, "f3a7c8e9")
        self.assertEqual(len(manifest.supported_providers), 1)


class TestReleaseCandidateBuilderE2E(unittest.TestCase):
    """Verifies full release builds runs and SQLite persistence."""

    def setUp(self) -> None:
        self.builder = ReleaseCandidateBuilder(db_path=":memory:")

    def test_build_flow(self) -> None:
        record = self.builder.build_release("1.0.0-rc.1", ReleaseType.RC)
        self.assertEqual(record.version, "1.0.0-rc.2")
        self.assertEqual(record.status, "success")
        self.assertEqual(len(record.artifacts), 2)

        # Check latest retrieval
        latest = self.builder.get_latest_build()
        self.assertIsNotNone(latest)
        self.assertEqual(latest["version"], "1.0.0-rc.2")

        # Check history
        history = self.builder.list_history()
        self.assertEqual(len(history), 1)
