"""Cost optimizer formulating suggestions to reduce token fees and LLM expenses."""

import uuid
from typing import List
from backend.execution_intelligence.models import (
    RecommendationModel,
    RecommendationCategory,
    ImpactLevel,
    ExecutionMetricsModel,
)


class CostOptimizer:
    """Analyzes token throughput and costs to recommend economical models and caching options."""

    @staticmethod
    def generate_recommendations(metrics: ExecutionMetricsModel) -> List[RecommendationModel]:
        """Examines metrics to identify context limits, cheaper models, or prompt reductions."""
        recommendations = []
        exec_count = metrics.execution_count or 1
        avg_cost = metrics.estimated_cost_usd / exec_count
        avg_tokens_in = metrics.total_tokens_in / exec_count

        # Check for model downgrade (e.g., if using expensive models like Claude 3.5 Sonnet / GPT-4o)
        if avg_cost > 0.08:
            recommendations.append(RecommendationModel(
                recommendation_id=f"rec-cost-{uuid.uuid4().hex[:6]}",
                category=RecommendationCategory.ALTERNATIVE_MODELS,
                description="Route non-critical steps to a lightweight model (e.g., GPT-4o-mini or Claude 3.5 Haiku).",
                rationale=f"High average cost (${avg_cost:.4f}) suggests simple sub-tasks could be offloaded to save budget.",
                estimated_cost_reduction_usd=avg_cost * 0.4,
                impact_level=ImpactLevel.HIGH
            ))

        # Check for Caching Opportunities
        if avg_tokens_in > 4000:
            recommendations.append(RecommendationModel(
                recommendation_id=f"rec-cache-{uuid.uuid4().hex[:6]}",
                category=RecommendationCategory.CACHING_OPPORTUNITIES,
                description="Enable context caching for repeated prompt components (system instructions, documents).",
                rationale=f"Average input of {avg_tokens_in:.0f} tokens indicates significant prefix duplication potential.",
                estimated_cost_reduction_usd=avg_cost * 0.3,
                impact_level=ImpactLevel.MEDIUM
            ))

        # Check for Context Reduction
        if avg_tokens_in > 8000:
            recommendations.append(RecommendationModel(
                recommendation_id=f"rec-ctx-{uuid.uuid4().hex[:6]}",
                category=RecommendationCategory.CONTEXT_REDUCTION,
                description="Implement semantic compression or summarization on long chat history / RAG evidence.",
                rationale="Excessively large inputs degrade performance and increase costs exponentially.",
                estimated_cost_reduction_usd=avg_cost * 0.25,
                impact_level=ImpactLevel.HIGH
            ))

        return recommendations
