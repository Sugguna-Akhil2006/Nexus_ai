"""Central analytics manager orchestrating metrics collection and aggregation."""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.analytics.cost_dashboard import CostDashboard
from backend.analytics.models import AggregateReport, MetricRecord, MetricType
from backend.analytics.provider_analytics import ProviderAnalytics
from backend.analytics.report_generator import ReportGenerator
from backend.analytics.trend_analyzer import TrendAnalyzer
from backend.analytics.usage_collector import UsageCollector
from backend.analytics.user_journey import UserJourney
from backend.analytics.workflow_analytics import WorkflowAnalytics


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AnalyticsManager:
    """Thread-safe singleton managing the usage collection and reporting pipelines."""

    _instance: Optional["AnalyticsManager"] = None

    def __new__(cls) -> "AnalyticsManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._ready = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_ready", False):
            return
        self._lock = threading.RLock()
        self._collector = UsageCollector()
        self._ready = True

    # ------------------------------------------------------------------
    # Collection
    # ------------------------------------------------------------------

    def record(
        self,
        metric_type: MetricType,
        name: str,
        value: float,
        context: Optional[Dict] = None,
    ) -> MetricRecord:
        """Saves a metric telemetry record."""
        return self._collector.collect(metric_type, name, value, context)

    def list_raw_metrics(self) -> List[MetricRecord]:
        """Lists all collected metrics."""
        return self._collector.list_metrics()

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def aggregate(self) -> AggregateReport:
        """Compiles raw metrics into an aggregated health and usage dashboard report."""
        with self._lock:
            records = self._collector.list_metrics()
            start = records[0].timestamp if records else _utcnow()
            end = records[-1].timestamp if records else _utcnow()

            return AggregateReport(
                start_time=start,
                end_time=end,
                workflow_metrics=WorkflowAnalytics.calculate(records),
                provider_metrics=ProviderAnalytics.calculate(records),
                intelligence_metrics={
                    "resume_usage": sum(1 for r in records if r.name == "resume_intelligence_usage"),
                    "github_usage": sum(1 for r in records if r.name == "github_intelligence_usage"),
                },
                resource_metrics={
                    "avg_cpu_pct": sum(r.value for r in records if r.name == "cpu_pct") / (sum(1 for r in records if r.name == "cpu_pct") or 1),
                },
                product_metrics=UserJourney.calculate(records),
            )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def generate_report(self, fmt: str = "json") -> str:
        """Formats the latest aggregate dashboard report."""
        rep = self.aggregate()
        f = fmt.lower()
        if f == "markdown":
            return ReportGenerator.to_markdown(rep)
        if f == "html":
            return ReportGenerator.to_html(rep)
        return ReportGenerator.to_json(rep)

    def cleanup(self) -> None:
        """Clears stored metrics for isolation."""
        with self._lock:
            self._collector.clear()
