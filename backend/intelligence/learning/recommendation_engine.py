"""Generates personalized settings recommendations and template suggestions."""

from datetime import datetime
from typing import List
from backend.runtime.event import Event, EventType, EventBus
from backend.intelligence.learning.experience_store import ExperienceStore


class RecommendationEngine:
    """Computes suggestion actions using preference counts and query patterns."""

    def __init__(self, store: ExperienceStore) -> None:
        self.store = store
        self.event_bus = EventBus()

    def generate_recommendations(self, workspace_id: str, detected_patterns: List[str]) -> List[str]:
        """Formulates suggested steps and publishes event logs."""
        recommendations = []

        # 1. Base suggestions on query patterns
        for pattern in detected_patterns:
            if "fastapi" in pattern.lower():
                recommendations.append("Recommended workflow: Run API Benchmark Comparison Template.")
            elif "resume" in pattern.lower():
                recommendations.append("Recommended workflow: Synchronize profile with UKP profile.")

        # 2. Add fallback recommendation if empty
        if not recommendations:
            recommendations.append("Recommended workflow: Initialize Multi-source Literature Review.")

        # Publish recommendation generated event
        self.event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="RecommendationEngine",
            payload={
                "event": "learning.recommendation.generated",
                "workspace_id": workspace_id,
                "recommendation_count": len(recommendations),
                "timestamp": datetime.utcnow().isoformat()
            }
        ))

        return recommendations
