"""Tests for marketplace search, sync, downloads, and package ratings."""

import unittest
from backend.marketplace.models import (
    MarketplacePackage,
    PackageMetadata,
    PackageType,
)
from backend.marketplace.package_registry import PackageRegistry
from backend.marketplace.rating_service import RatingService
from backend.marketplace.marketplace_client import MarketplaceClient


class TestSyncRatings(unittest.TestCase):
    """Verifies rating computation, downloads metrics, and catalog searching."""

    def setUp(self) -> None:
        self.registry = PackageRegistry()
        self.rating_service = RatingService(self.registry)
        self.client = MarketplaceClient(self.registry)

        # Register a test package
        self.meta = PackageMetadata(
            package_id="data_connector",
            version="1.0.0",
            author="Google DeepMind",
            license="MIT",
            description="High speed data connector",
        )
        self.pkg = MarketplacePackage(
            metadata=self.meta,
            package_type=PackageType.CONNECTOR,
            publisher="Google DeepMind"
        )
        self.registry.register_package(self.pkg)

    def test_search_and_fetch(self) -> None:
        """Tests text and type based searches on client."""
        results = self.client.search("connector", PackageType.CONNECTOR)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata.package_id, "data_connector")

        # Search mismatch
        results_mismatch = self.client.search("theme")
        self.assertEqual(len(results_mismatch), 0)

        # Get details
        details = self.client.get_details("data_connector")
        self.assertIsNotNone(details)
        self.assertEqual(details.metadata.version, "1.0.0")

    def test_ratings_calculation(self) -> None:
        """Tests that rating averages update correctly with multiple submissions."""
        # Score 4 from User 1
        self.rating_service.submit_rating("data_connector", "1.0.0", "user_1", 4, "Good")
        details = self.client.get_details("data_connector")
        self.assertEqual(details.average_rating, 4.0)
        self.assertEqual(details.ratings_count, 1)

        # Score 5 from User 2
        self.rating_service.submit_rating("data_connector", "1.0.0", "user_2", 5, "Excellent")
        self.assertEqual(details.average_rating, 4.5)
        self.assertEqual(details.ratings_count, 2)

        # Update rating from User 1 to 2
        self.rating_service.submit_rating("data_connector", "1.0.0", "user_1", 2, "Disappointed")
        self.assertEqual(details.average_rating, 3.5)
        self.assertEqual(details.ratings_count, 2)

    def test_downloads_tracking(self) -> None:
        """Tests that downloads increments work across the registry."""
        details = self.client.get_details("data_connector")
        self.assertEqual(details.downloads, 0)

        self.rating_service.increment_downloads("data_connector")
        self.assertEqual(details.downloads, 1)
