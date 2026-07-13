"""Unit tests for Platform Metrics collection service."""

import unittest

from backend.platform.hardening.metrics_collector import MetricsCollector


class TestPlatformMetrics(unittest.TestCase):
    """Test suite covering operational metrics registration and aggregates."""

    def test_metrics_collection(self) -> None:
        """Verifies counts are recorded and endpoints map correctly."""
        metrics = MetricsCollector()
        metrics.clear()

        metrics.increment("db_queries_total", 5)
        metrics.increment_endpoint("/api/chat")
        
        all_metrics = metrics.get_all_metrics()
        self.assertEqual(all_metrics["db_queries_total"], 5)
        self.assertEqual(all_metrics["api_requests_total"], 1)
        self.assertEqual(all_metrics["api_requests_by_endpoint"]["/api/chat"], 1)
