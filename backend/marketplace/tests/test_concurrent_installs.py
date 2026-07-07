"""Tests for concurrent installations and thread safety."""

import concurrent.futures
import unittest
from backend.marketplace.models import PackageMetadata, PackageType, MarketplacePackage
from backend.marketplace.marketplace_service import MarketplaceService


class TestConcurrentInstalls(unittest.TestCase):
    """Verifies that multiple concurrent package installations execute without race conditions."""

    def test_concurrent_installs(self) -> None:
        """Concurrently installs multiple packages to verify thread safety."""
        service = MarketplaceService()

        # Pre-register packages in the registry
        for i in range(15):
            p_id = f"pkg_{i}"
            meta = PackageMetadata(
                package_id=p_id,
                version="1.0.0",
                author="Partner",
                license="MIT",
                description=f"Package {i}",
                digital_signature=f"sig:{p_id}:1.0.0:fp_partner_key_2026",
                checksum=f"mock_checksum_{i}"
            )
            pkg = MarketplacePackage(
                metadata=meta,
                package_type=PackageType.PLUGIN,
                publisher="Official Partner"
            )
            service.registry.register_package(pkg)
            
            # Mock the verifications to accept any checksum/signature for the concurrent test
            service.verifier.publisher_keys["Official Partner"] = "fp_partner_key_2026"

        # Mock verifier methods so we can test concurrency without needing real content byte hashing
        service.verifier.verify_checksum = lambda meta, content: True
        service.verifier.verify_signature = lambda meta, pub: True

        def run_install(idx: int) -> str:
            installed = service.install_package(f"pkg_{idx}", "1.0.0")
            return installed.metadata.package_id

        # Execute concurrent installs
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_install, i) for i in range(15)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertEqual(len(results), 15)
        for i in range(15):
            self.assertIn(f"pkg_{i}", results)
            installed_pkg = service.package_manager.get_installed(f"pkg_{i}")
            self.assertIsNotNone(installed_pkg)
            self.assertEqual(installed_pkg.metadata.version, "1.0.0")
