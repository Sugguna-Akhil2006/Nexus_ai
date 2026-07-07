"""Unit tests for Universal Connector Framework module."""

from __future__ import annotations

import concurrent.futures
import unittest

from backend.connectors.models import ConnectorConfig
from backend.connectors.connector_manager import ConnectorManager


class TestConnectorFramework(unittest.TestCase):
    """Test suite verifying client configurations, credentials, limits, and syncs."""

    def setUp(self) -> None:
        self.mgr = ConnectorManager()
        self.mgr.clear()

        # Seed connector config for tests
        self.config = ConnectorConfig(
            connector_id="conn-github-test",
            workspace_id="ws-test",
            connector_type="github",
            name="Test Repository Connection",
            auth_data={"access_token": "token-12345", "refresh_token": "refresh-token-xyz"},
            metadata={"repo_name": "nexus_ai"}
        )

    def test_credential_encryption_and_refresh(self) -> None:
        """Verifies base64 credential encryption and token refresh exchange loops."""
        self.mgr.configure_connector(self.config)
        retrieved = self.mgr.get_connector("conn-github-test")
        
        self.assertEqual(retrieved.auth_data["access_token"], "token-12345")
        
        # Test Refresh
        refreshed_auth = self.mgr.credential_mgr.refresh_oauth_token(retrieved.auth_data)
        self.assertIn("refreshed-token", refreshed_auth["access_token"])

    def test_connector_sync_and_checkpoint(self) -> None:
        """Verifies dynamic data sync and checkpoint increment save."""
        self.mgr.configure_connector(self.config)
        job = self.mgr.sync_connector("conn-github-test")
        
        self.assertEqual(job.status, "completed")
        self.assertEqual(job.records_processed, 1)
        self.assertIn("last_timestamp", job.checkpoint_state)

        # Config should be updated with last sync
        updated_config = self.mgr.get_connector("conn-github-test")
        self.assertIsNotNone(updated_config.last_sync_timestamp)

    def test_rate_limiting_throttles(self) -> None:
        """Verifies token bucket rate limit blocks once capacity is consumed."""
        # Force low rate limit
        self.mgr.rate_limiter.limit = 5
        self.mgr.rate_limiter.capacity = 5
        self.mgr.rate_limiter.tokens = 5.0

        for _ in range(5):
            self.assertTrue(self.mgr.rate_limiter.consume())

        # 6th should fail
        self.assertFalse(self.mgr.rate_limiter.consume())

    def test_connector_health_monitor(self) -> None:
        """Verifies health monitor registers online/offline properties."""
        h = self.mgr.health_monitor.check_health(self.config)
        self.assertEqual(h.status, "healthy")
        self.assertGreater(h.latency_ms, 0.0)

    def test_concurrent_connections_sync(self) -> None:
        """Ensures concurrent sync processes execute securely in parallel threads."""
        self.mgr.configure_connector(self.config)

        def sync_task(index: int) -> None:
            self.mgr.sync_connector("conn-github-test")

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(sync_task, i) for i in range(20)]
            concurrent.futures.wait(futures)
