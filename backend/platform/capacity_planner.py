"""Capacity Planner predicting future workload limits and load thresholds."""

from __future__ import annotations

from typing import Dict, Optional

from backend.platform.usage_analytics import UsageAnalytics


class CapacityPlanner:
    """Estimates workspace capacity margins based on operational usage patterns."""

    def __init__(self, analytics: Optional[UsageAnalytics] = None) -> None:
        self.analytics = analytics or UsageAnalytics()

    def get_projections(self) -> Dict[str, Any]:
        """Calculates forecasted tokens and requests growth models."""
        summary = self.analytics.get_metrics_summary()
        
        # Simple projection: predict 1.5x scaling
        current_req = summary.total_requests
        predicted_growth = int(current_req * 1.5)

        return {
            "current_requests": current_req,
            "projected_monthly_requests": predicted_growth,
            "is_within_limits": True if current_req < 10000 else False,
            "recommended_concurrency_workers": 30 if current_req < 500 else 60
        }
