"""Comprehensive unit and E2E tests for the Platform Analytics system."""

from __future__ import annotations

import threading
import unittest

from backend.analytics.models import (
    MetricType,
)
from backend.analytics.usage_collector import UsageCollector
from backend.analytics.metrics_aggregator import MetricsAggregator
from backend.analytics.workflow_analytics import WorkflowAnalytics
from backend.analytics.provider_analytics import ProviderAnalytics
from backend.analytics.user_journey import UserJourney
from backend.analytics.cost_dashboard import CostDashboard
from backend.analytics.trend_analyzer import TrendAnalyzer
from backend.analytics.report_generator import ReportGenerator
from backend.analytics.analytics_manager import AnalyticsManager


class TestMetricsAggregator(unittest.TestCase):
    """Verifies metrics mathematical aggregates."""

    def test_average_and_sum(self) -> None:
        collector = UsageCollector()
        collector.collect(MetricType.RESOURCE, "cpu_pct", 10.0)
        collector.collect(MetricType.RESOURCE, "cpu_pct", 20.0)
        metrics = collector.list_metrics()

        self.assertEqual(MetricsAggregator.get_average(metrics, "cpu_pct"), 15.0)
        self.assertEqual(MetricsAggregator.get_sum(metrics, "cpu_pct"), 30.0)
        self.assertEqual(MetricsAggregator.get_count(metrics, "cpu_pct"), 2)


class TestWorkflowAnalytics(unittest.TestCase):
    """Verifies workflow success and duration metrics aggregation."""

    def test_workflow_stats(self) -> None:
        collector = UsageCollector()
        collector.collect(MetricType.WORKFLOW, "workflow_run", 1.0, {"status": "success"})
        collector.collect(MetricType.WORKFLOW, "workflow_run", 1.0, {"status": "failure"})
        collector.collect(MetricType.WORKFLOW, "workflow_duration_ms", 500.0)
        metrics = collector.list_metrics()

        stats = WorkflowAnalytics.calculate(metrics)
        self.assertEqual(stats["total_runs"], 2)
        self.assertEqual(stats["success_rate"], 0.5)
        self.assertEqual(stats["avg_duration_ms"], 500.0)


class TestProviderAnalytics(unittest.TestCase):
    """Verifies provider cost and token volumes aggregates."""

    def test_provider_stats(self) -> None:
        collector = UsageCollector()
        collector.collect(MetricType.PROVIDER, "provider_cost_usd", 0.05)
        collector.collect(MetricType.PROVIDER, "provider_tokens", 1000.0)
        collector.collect(MetricType.PROVIDER, "provider_latency_ms", 120.0)
        metrics = collector.list_metrics()

        stats = ProviderAnalytics.calculate(metrics)
        self.assertEqual(stats["total_cost_usd"], 0.05)
        self.assertEqual(stats["total_tokens_consumed"], 1000)
        self.assertEqual(stats["avg_latency_ms"], 120.0)


class TestCostDashboard(unittest.TestCase):
    """Verifies budget threshold warnings."""

    def test_cost_warnings(self) -> None:
        collector = UsageCollector()
        collector.collect(MetricType.PROVIDER, "provider_cost_usd", 90.0)
        metrics = collector.list_metrics()

        stats = CostDashboard.calculate(metrics)
        self.assertTrue(stats["warning"])
        self.assertEqual(stats["pct_consumed"], 90.0)


class TestTrendAnalyzer(unittest.TestCase):
    """Verifies daily metric grouping trends."""

    def test_daily_trends(self) -> None:
        collector = UsageCollector()
        collector.collect(MetricType.RESOURCE, "cpu_pct", 10.0)
        metrics = collector.list_metrics()

        stats = TrendAnalyzer.calculate(metrics)
        self.assertIn("daily_trends", stats)


class TestAnalyticsManagerE2E(unittest.TestCase):
    """E2E workflow analytics operations, dashboard reports, and thread safety."""

    def setUp(self) -> None:
        self.manager = AnalyticsManager()
        self.manager.cleanup()

    def test_record_and_aggregate(self) -> None:
        self.manager.record(MetricType.WORKFLOW, "workflow_run", 1.0, {"status": "success"})
        self.manager.record(MetricType.PROVIDER, "provider_cost_usd", 0.002)

        rep = self.manager.aggregate()
        self.assertEqual(rep.workflow_metrics["total_runs"], 1)
        self.assertEqual(rep.provider_metrics["total_cost_usd"], 0.002)

    def test_generate_report_markdown(self) -> None:
        self.manager.record(MetricType.WORKFLOW, "workflow_run", 1.0, {"status": "success"})
        md = self.manager.generate_report("markdown")
        self.assertIn("# Nexus AI Platform Usage Analytics Report", md)

    def test_generate_report_html(self) -> None:
        self.manager.record(MetricType.WORKFLOW, "workflow_run", 1.0, {"status": "success"})
        html = self.manager.generate_report("html")
        self.assertIn("<!DOCTYPE html>", html)

    def test_concurrency_record(self) -> None:
        errors = []

        def worker(i: int) -> None:
            try:
                self.manager.record(MetricType.RESOURCE, "cpu_pct", float(i))
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        metrics = self.manager.list_raw_metrics()
        self.assertEqual(len(metrics), 50)
