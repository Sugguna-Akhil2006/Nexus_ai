"""Unit tests for Operations Monitoring and Telemetry package."""

import unittest

from backend.ops.monitoring.prometheus_metrics import PrometheusMetrics
from backend.ops.monitoring.service_monitor import ServiceMonitor


class TestOpsMonitoring(unittest.TestCase):
    """Test suite covering Prometheus scrapers formatting and health status aggregators."""

    def test_prometheus_formatting(self) -> None:
        """Verifies counters increment and format into scrapable text block."""
        pm = PrometheusMetrics()
        pm.clear()

        pm.increment("http_requests_total", 3.0)
        pm.increment("db_queries_total", 12.0)
        
        text = pm.get_metrics_text()
        self.assertIn("http_requests_total 3.0", text)
        self.assertIn("db_queries_total 12.0", text)

    def test_service_monitor_aggregates(self) -> None:
        """Verifies consolidated health and resource metrics return."""
        sm = ServiceMonitor()
        summary = sm.get_summary()
        
        self.assertIn("status", summary)
        self.assertIn("database", summary)
        self.assertIn("resources", summary)
