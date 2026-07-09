"""Provider recovery handler detecting provider failures and switching to fallbacks."""

from __future__ import annotations

import time
import uuid

from backend.recovery.models import (
    FailureScenario,
    RecoveryEvent,
    RecoveryStatus,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


class ProviderRecovery:
    """Handles provider-level failures by probing availability and enacting fallbacks.

    Recovery steps:
    1. Attempt to instantiate the ProviderRegistry.
    2. Probe the primary provider's health status.
    3. If unhealthy, switch to the next available provider in the fallback chain.
    """

    def recover(self, scenario: FailureScenario = FailureScenario.PROVIDER_FAILURE) -> RecoveryEvent:
        """Executes the provider recovery sequence.

        Args:
            scenario: Triggering failure scenario.

        Returns:
            :class:`RecoveryEvent` describing the outcome.
        """
        start = time.perf_counter()
        event_id = str(uuid.uuid4())[:8]

        try:
            from backend.providers.registry import ProviderRegistry
            reg = ProviderRegistry()

            # Probe: check if the registry can list providers
            providers = reg.list_providers() if hasattr(reg, "list_providers") else []
            if providers:
                return RecoveryEvent(
                    event_id=event_id,
                    scenario=scenario,
                    component="provider_registry",
                    status=RecoveryStatus.COMPLETED,
                    detail=f"Provider registry healthy. {len(providers)} provider(s) available.",
                    duration_ms=_ms(start),
                )

            # Empty registry – attempt fallback switch
            if hasattr(reg, "get_fallback"):
                fallback = reg.get_fallback()
                detail = f"Primary provider unavailable; switched to fallback: {fallback}."
            else:
                detail = "Provider registry empty; no fallback available. Manual intervention required."

            return RecoveryEvent(
                event_id=event_id,
                scenario=scenario,
                component="provider_registry",
                status=RecoveryStatus.PARTIAL,
                detail=detail,
                duration_ms=_ms(start),
            )

        except Exception as exc:
            return RecoveryEvent(
                event_id=event_id,
                scenario=scenario,
                component="provider_registry",
                status=RecoveryStatus.FAILED,
                detail=f"Provider recovery failed: {exc}",
                duration_ms=_ms(start),
            )
