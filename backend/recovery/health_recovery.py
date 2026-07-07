"""Health recovery handler verifying platform subsystems post-restart."""

from __future__ import annotations

import time
import uuid
from typing import List, Tuple

from backend.recovery.models import (
    FailureScenario,
    RecoveryEvent,
    RecoveryStatus,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


class HealthRecovery:
    """Runs a post-failure health probe across platform subsystems.

    Each subsystem is probed independently.  Failures in one subsystem do
    not prevent the remaining checks from running.  The final event status
    reflects the worst result across all probes.
    """

    SUBSYSTEMS = [
        ("SQLite Storage", "_probe_storage"),
        ("Intelligence Registry", "_probe_registry"),
        ("EventBus", "_probe_event_bus"),
        ("Workflow Template Library", "_probe_template_library"),
    ]

    def recover(
        self,
        scenario: FailureScenario = FailureScenario.APPLICATION_RESTART,
    ) -> RecoveryEvent:
        """Probes all subsystems and returns a consolidated recovery event.

        Args:
            scenario: Triggering failure scenario.

        Returns:
            :class:`RecoveryEvent`.
        """
        start = time.perf_counter()
        event_id = str(uuid.uuid4())[:8]
        results: List[Tuple[str, bool, str]] = []

        for name, method_name in self.SUBSYSTEMS:
            probe = getattr(self, method_name)
            ok, detail = probe()
            results.append((name, ok, detail))

        healthy = [r[0] for r in results if r[1]]
        unhealthy = [f"{r[0]}: {r[2]}" for r in results if not r[1]]

        status = RecoveryStatus.COMPLETED if not unhealthy else (
            RecoveryStatus.PARTIAL if healthy else RecoveryStatus.FAILED
        )
        detail = (
            f"{len(healthy)}/{len(results)} subsystems healthy."
            + (f" Issues: {'; '.join(unhealthy)}" if unhealthy else "")
        )

        return RecoveryEvent(
            event_id=event_id,
            scenario=scenario,
            component="platform_health",
            status=status,
            detail=detail,
            duration_ms=_ms(start),
        )

    # ------------------------------------------------------------------
    # Subsystem probes
    # ------------------------------------------------------------------

    @staticmethod
    def _probe_storage() -> Tuple[bool, str]:
        try:
            from backend.api.sqlite_mock import DBStorage
            db = DBStorage()
            db.get_user("admin")
            return True, "OK"
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _probe_registry() -> Tuple[bool, str]:
        try:
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            reg.list_modules()
            return True, "OK"
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _probe_event_bus() -> Tuple[bool, str]:
        try:
            from backend.runtime.event import EventBus
            EventBus()
            return True, "OK"
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _probe_template_library() -> Tuple[bool, str]:
        try:
            from backend.workflow_library.template_registry import TemplateRegistry
            TemplateRegistry(db_path=":memory:").list_templates()
            return True, "OK"
        except Exception as exc:
            return False, str(exc)
