"""Latency optimizer proposing parallel execution and workflow restructuring suggestions."""

import uuid
from typing import List
from backend.execution_intelligence.models import (
    RecommendationModel,
    RecommendationCategory,
    ImpactLevel,
    ExecutionMetricsModel,
)


class LatencyOptimizer:
    """Analyzes execution sequences and provider delays to optimize latency."""

    @staticmethod
    def generate_recommendations(metrics: ExecutionMetricsModel) -> List[RecommendationModel]:
        """Analyzes duration metrics to suggest parallel steps, faster models, or connector tweaks."""
        recommendations = []
        exec_count = metrics.execution_count or 1
        avg_dur = metrics.average_duration_ms

        # 1. Parallel Execution
        # If there are multiple modules taking significant time, they could potentially run in parallel.
        if len(metrics.module_execution_times) >= 3 and avg_dur > 3000:
            recommendations.append(RecommendationModel(
                recommendation_id=f"rec-parallel-{uuid.uuid4().hex[:6]}",
                category=RecommendationCategory.PARALLEL_EXECUTION,
                description="Execute independent workflow steps in parallel using concurrent execution blocks.",
                rationale="Serialized processing of independent tasks increases overall workflow latency.",
                estimated_speedup_pct=35.0,
                impact_level=ImpactLevel.HIGH
            ))

        # 2. Caching Opportunities for slow static modules
        for mod, duration in metrics.module_execution_times.items():
            avg_mod_dur = duration / exec_count
            if avg_mod_dur > 2000:
                recommendations.append(RecommendationModel(
                    recommendation_id=f"rec-cache-lat-{uuid.uuid4().hex[:6]}",
                    category=RecommendationCategory.CACHING_OPPORTUNITIES,
                    description=f"Enable response caching for slow module '{mod}'.",
                    rationale=f"Module '{mod}' averages {avg_mod_dur:.1f}ms runtime, causing significant blocking latency.",
                    estimated_speedup_pct=20.0,
                    impact_level=ImpactLevel.MEDIUM
                ))
                break

        # 3. Connector Improvements
        # Check if there is provider latency that is high
        for provider, latencies in metrics.provider_latencies.items():
            if latencies:
                avg_lat = sum(latencies) / len(latencies)
                if avg_lat > 4000:
                    recommendations.append(RecommendationModel(
                        recommendation_id=f"rec-conn-{uuid.uuid4().hex[:6]}",
                        category=RecommendationCategory.CONNECTOR_IMPROVEMENTS,
                        description=f"Optimize connection pooling / reduce timeouts for provider '{provider}' connector.",
                        rationale=f"LLM provider '{provider}' shows high latency (avg {avg_lat:.1f}ms). Consider streaming responses or switching regions.",
                        estimated_speedup_pct=15.0,
                        impact_level=ImpactLevel.MEDIUM
                    ))

        return recommendations
