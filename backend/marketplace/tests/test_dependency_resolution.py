"""Tests for topological dependency resolution and constraint checking."""

import unittest
from backend.marketplace.models import PackageMetadata
from backend.marketplace.dependency_manager import DependencyManager, DependencyResolutionError


class TestDependencyResolution(unittest.TestCase):
    """Verifies that DependencyManager correctly resolves dependency graphs."""

    def test_simple_resolution(self) -> None:
        """Tests standard A depends on B depends on C graph."""
        available = {
            "pkg_a": [
                PackageMetadata(
                    package_id="pkg_a", version="1.0.0", author="A", license="MIT", description="",
                    dependencies={"pkg_b": ">=2.0.0"}
                )
            ],
            "pkg_b": [
                PackageMetadata(
                    package_id="pkg_b", version="2.0.0", author="B", license="MIT", description="",
                    dependencies={"pkg_c": "~=1.1.0"}
                )
            ],
            "pkg_c": [
                PackageMetadata(
                    package_id="pkg_c", version="1.1.5", author="C", license="MIT", description=""
                )
            ]
        }

        mgr = DependencyManager(available)
        resolved = mgr.resolve_dependencies("pkg_a", "1.0.0")
        
        # Output should be dependencies first: C, B, A
        self.assertEqual(len(resolved), 3)
        self.assertEqual(resolved[0].package_id, "pkg_c")
        self.assertEqual(resolved[1].package_id, "pkg_b")
        self.assertEqual(resolved[2].package_id, "pkg_a")

    def test_missing_dependency(self) -> None:
        """Tests that resolution fails if a required dependency is missing."""
        available = {
            "pkg_a": [
                PackageMetadata(
                    package_id="pkg_a", version="1.0.0", author="A", license="MIT", description="",
                    dependencies={"pkg_missing": "*"}
                )
            ]
        }
        mgr = DependencyManager(available)
        with self.assertRaises(DependencyResolutionError):
            mgr.resolve_dependencies("pkg_a", "1.0.0")

    def test_circular_dependency(self) -> None:
        """Tests that resolution fails on circular references."""
        available = {
            "pkg_a": [
                PackageMetadata(
                    package_id="pkg_a", version="1.0.0", author="A", license="MIT", description="",
                    dependencies={"pkg_b": "*"}
                )
            ],
            "pkg_b": [
                PackageMetadata(
                    package_id="pkg_b", version="1.0.0", author="B", license="MIT", description="",
                    dependencies={"pkg_a": "*"}
                )
            ]
        }
        mgr = DependencyManager(available)
        with self.assertRaises(DependencyResolutionError):
            mgr.resolve_dependencies("pkg_a", "1.0.0")

    def test_version_conflict(self) -> None:
        """Tests version conflict resolution errors."""
        available = {
            "pkg_a": [
                PackageMetadata(
                    package_id="pkg_a", version="1.0.0", author="A", license="MIT", description="",
                    dependencies={"pkg_b": ">=2.0.0", "pkg_c": ">=1.0.0"}
                )
            ],
            # C requires B to be an older version (<1.5.0) which conflicts with A's requirement of B>=2.0.0
            "pkg_c": [
                PackageMetadata(
                    package_id="pkg_c", version="1.0.0", author="C", license="MIT", description="",
                    dependencies={"pkg_b": "<1.5.0"}
                )
            ],
            "pkg_b": [
                PackageMetadata(package_id="pkg_b", version="1.2.0", author="B", license="MIT", description=""),
                PackageMetadata(package_id="pkg_b", version="2.0.0", author="B", license="MIT", description="")
            ]
        }
        mgr = DependencyManager(available)
        with self.assertRaises(DependencyResolutionError):
            mgr.resolve_dependencies("pkg_a", "1.0.0")
