"""Workflow recommender combining cost, latency, and system suggestions and raising events."""

from typing import List
from backend.execution_intelligence.models import RecommendationModel, ExecutionMetricsModel
from backend.execution_intelligence.cost_optimizer import CostOptimizer
from backend.execution_intelligence.latency_optimizer import LatencyOptimizer
from backend.runtime.event import Event, EventBus, EventType, EventPriority


class WorkflowRecommender:
    """Collates diverse recommendations, ranks them, and triggers event updates."""

    def __init__(self) -> None:
        self._event_bus = EventBus()

    def generate_all_recommendations(self, metrics: ExecutionMetricsModel) -> List[RecommendationModel]:
        """Runs child optimization pipelines and publishes created recommendations."""
        recommendations: List[RecommendationModel] = []
        
        # Pull cost suggestions
        cost_recs = CostOptimizer.generate_recommendations(metrics)
        recommendations.extend(cost_recs)

        # Pull latency suggestions
        latency_recs = LatencyOptimizer.generate_recommendations(metrics)
        recommendations.extend(latency_recs)

        # Broadcast recommendations to the system
        for rec in recommendations:
            self._event_bus.publish(Event(
                event_type=EventType.RECOMMENDATION_GENERATED,
                priority=EventPriority.NORMAL,
                payload={
                    "recommendation_id": rec.recommendation_id,
                    "category": rec.category.value,
                    "impact_level": rec.impact_level.value,
                    "description": rec.description
                }
            ))

        return recommendations
