"""User journey tracker monitoring feature popularity and drop-off points."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from backend.analytics.models import MetricRecord, MetricType


class UserJourney:
    """Calculates user feature usage frequency and drop-off points."""

    @staticmethod
    def calculate(records: List[MetricRecord]) -> Dict[str, Any]:
        """Calculates hit rates per feature and drop-off indices."""
        prod = [r for r in records if r.metric_type == MetricType.PRODUCT]

        clicks = defaultdict(int)
        for r in prod:
            clicks[r.name] += 1

        # Sorted dictionary from popular to least
        sorted_popularity = dict(sorted(clicks.items(), key=lambda item: item[1], reverse=True))

        return {
            "popular_features": sorted_popularity,
            "drop_offs": {
                "step_1_upload": sum(1 for r in prod if r.name == "upload"),
                "step_2_analyze": sum(1 for r in prod if r.name == "analyze"),
            },
        }
