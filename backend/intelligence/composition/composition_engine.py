"""Composition engine — the unified public API for the composition layer.

Exposes three operations:
- ``compose``  : Combine N module responses into one ``ComposedResponse``.
- ``merge``    : Merge two existing ``ComposedResponse`` objects.
- ``compare``  : Produce a side-by-side comparison report for two responses.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional

from backend.intelligence.composition.confidence_aggregator import ConfidenceAggregator
from backend.intelligence.composition.conflict_detector import ConflictDetector
from backend.intelligence.composition.models import (
    ComposedResponse,
    CompositionStatus,
    ConfidenceStrategy,
    ConflictRecord,
)
from backend.intelligence.composition.response_synthesizer import ResponseSynthesizer
from backend.intelligence.contracts.response_models import IntelligenceResponse
from backend.runtime.event import Event, EventBus, EventPriority, EventType


class CompositionEngine:
    """Thread-safe facade for the Intelligence Composition Layer.

    Args:
        strategy:              Default confidence-aggregation strategy.
        auto_resolve_conflicts: Whether to auto-resolve detected conflicts.
        event_bus:             Optional override for the singleton EventBus.
    """

    def __init__(
        self,
        strategy: ConfidenceStrategy = ConfidenceStrategy.WEIGHTED_AVERAGE,
        auto_resolve_conflicts: bool = True,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self._strategy = strategy
        self._auto_resolve = auto_resolve_conflicts
        self._bus = event_bus or EventBus()
        self._lock = threading.RLock()
        self._history: Dict[str, ComposedResponse] = {}  # composition_id → result

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def compose(
        self,
        request_id: str,
        responses: List[IntelligenceResponse],
        strategy: Optional[ConfidenceStrategy] = None,
        manual_weights: Optional[Dict[str, float]] = None,
    ) -> ComposedResponse:
        """Composes multiple module responses into one unified report.

        Args:
            request_id:     Originating request identifier.
            responses:      Module ``IntelligenceResponse`` objects.
            strategy:       Per-call confidence strategy override.
            manual_weights: Optional per-module weight map for WEIGHTED_AVERAGE.

        Returns:
            ``ComposedResponse`` with all sections populated.
        """
        with self._lock:
            synthesizer = ResponseSynthesizer(
                strategy=strategy or self._strategy,
                manual_weights=manual_weights,
                auto_resolve_conflicts=self._auto_resolve,
            )
            result = synthesizer.synthesize(request_id, responses)
            self._history[result.composition_id] = result

        self._bus.publish(Event(
            event_type=EventType.ANALYSIS_COMPLETED,
            priority=EventPriority.NORMAL,
            payload={
                "composition_id": result.composition_id,
                "request_id": request_id,
                "modules": result.participating_modules,
                "confidence": (
                    result.aggregated_confidence.overall
                    if result.aggregated_confidence else 0.0
                ),
                "conflicts": len(result.conflicts),
                "status": result.status.value,
            },
        ))
        return result

    def merge(
        self,
        base: ComposedResponse,
        additional: ComposedResponse,
    ) -> ComposedResponse:
        """Merges an additional ``ComposedResponse`` into a base response.

        Useful when new modules complete asynchronously after the first
        composition pass.

        Args:
            base:       The existing composed response.
            additional: A newer composed response to merge in.

        Returns:
            A new ``ComposedResponse`` combining both.
        """
        # Combine all contributions into a flat module response list and re-compose
        all_modules = list(
            {mc.module for mc in base.module_contributions}
            | {mc.module for mc in additional.module_contributions}
        )
        # Build synthetic IntelligenceResponse objects from the contributions
        synthetic: List[IntelligenceResponse] = []
        for mc in base.module_contributions + additional.module_contributions:
            synthetic.append(IntelligenceResponse(
                execution_id=mc.execution_id,
                request_id=base.request_id,
                module=mc.module,
                status=mc.status,
                confidence=mc.confidence,
                summary=mc.summary,
                structured_output=mc.structured_output,
            ))

        return self.compose(base.request_id, synthetic)

    def compare(
        self,
        left: ComposedResponse,
        right: ComposedResponse,
    ) -> Dict[str, Any]:
        """Produces a side-by-side comparison of two composed responses.

        Args:
            left:  Baseline composed response.
            right: Comparison composed response.

        Returns:
            Comparison report dict with delta fields, conflict diffs, and
            confidence comparison.
        """
        left_modules = set(left.participating_modules)
        right_modules = set(right.participating_modules)

        conf_left = left.aggregated_confidence.overall if left.aggregated_confidence else 0.0
        conf_right = right.aggregated_confidence.overall if right.aggregated_confidence else 0.0

        return {
            "left_composition_id": left.composition_id,
            "right_composition_id": right.composition_id,
            "modules": {
                "only_in_left": sorted(left_modules - right_modules),
                "only_in_right": sorted(right_modules - left_modules),
                "shared": sorted(left_modules & right_modules),
            },
            "confidence": {
                "left": conf_left,
                "right": conf_right,
                "delta": round(conf_right - conf_left, 4),
                "winner": "right" if conf_right > conf_left else "left",
            },
            "conflicts": {
                "left_count": len(left.conflicts),
                "right_count": len(right.conflicts),
            },
            "findings": {
                "left_count": len(left.detailed_findings),
                "right_count": len(right.detailed_findings),
            },
            "recommendations": {
                "left_count": len(left.recommendations),
                "right_count": len(right.recommendations),
            },
            "metrics": {
                "left_duration_ms": left.total_duration_ms,
                "right_duration_ms": right.total_duration_ms,
                "left_cost_usd": left.estimated_cost_usd,
                "right_cost_usd": right.estimated_cost_usd,
            },
        }

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_composed(self, composition_id: str) -> Optional[ComposedResponse]:
        """Returns a previously composed result by ID."""
        with self._lock:
            return self._history.get(composition_id)

    def list_compositions(self) -> List[str]:
        """Returns all stored composition IDs."""
        with self._lock:
            return list(self._history.keys())
