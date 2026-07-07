"""Provider tracker monitoring AI provider latencies, token consumption, and fallback rates."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.diagnostics.models import ProviderMetricSummary


class ProviderTracker:
    """Thread-safe registry logging call telemetry for each registered LLM/vector provider."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._summaries: Dict[str, ProviderMetricSummary] = {}

    def log_call(
        self,
        provider: str,
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        failed: bool = False,
        fallback_occurred: bool = False,
    ) -> None:
        """Records telemetry details of a single provider call."""
        with self._lock:
            summary = self._summaries.get(provider)
            if not summary:
                summary = ProviderMetricSummary(provider_name=provider)
                self._summaries[provider] = summary

            # Accumulate metrics
            total_time = (summary.avg_latency_ms * summary.total_calls) + latency_ms
            summary.total_calls += 1
            summary.avg_latency_ms = round(total_time / summary.total_calls, 2)

            summary.total_tokens_in += tokens_in
            summary.total_tokens_out += tokens_out

            if failed:
                summary.failures += 1
            if fallback_occurred:
                summary.fallbacks += 1

            # Re-evaluate fallback rate
            summary.fallback_rate = round(summary.fallbacks / summary.total_calls, 4)

    def get_summary(self, provider: str) -> Optional[ProviderMetricSummary]:
        """Returns the summary metrics for a given provider."""
        with self._lock:
            return self._summaries.get(provider)

    def list_summaries(self) -> List[ProviderMetricSummary]:
        """Returns summaries for all tracked providers."""
        with self._lock:
            return list(self._summaries.values())
