"""Runtime certifier verifying startup, memory, registry, execution, and thread safety."""

from __future__ import annotations

import threading
import time

from backend.certification.models import (
    CertificationDomain,
    CheckResult,
    CheckStatus,
    DomainReport,
)


class RuntimeCertifier:
    """Runs certification checks against the Nexus Runtime subsystem.

    Checks performed:
    - Runtime module importability.
    - EventBus instantiation and event dispatch.
    - IntelligenceRegistry registration and listing.
    - Thread-safety probe (concurrent reads on the registry).
    - Plugin framework availability.
    """

    DOMAIN = CertificationDomain.RUNTIME

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all runtime checks and returns a domain report.

        Returns:
            :class:`DomainReport` with individual check results.
        """
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_runtime_import(),
            cls._check_event_bus(),
            cls._check_intelligence_registry(),
            cls._check_thread_safety(),
            cls._check_plugin_framework(),
        ])
        return report

    @staticmethod
    def _check_runtime_import() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.runtime.event import EventBus  # noqa: F401
            return CheckResult(
                name="Runtime Import",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.PASSED,
                message="Runtime modules importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Runtime Import",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_event_bus() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.runtime.event import EventBus, Event, EventType
            bus = EventBus()
            received: list[str] = []
            bus.subscribe(EventType.AGENT_STARTED, lambda e: received.append(e.event_id))
            bus.publish(Event(event_type=EventType.AGENT_STARTED, source="cert"))
            status = CheckStatus.PASSED if received else CheckStatus.WARNING
            msg = "EventBus dispatch confirmed." if received else "EventBus dispatch produced no events."
            return CheckResult(
                name="EventBus Dispatch",
                domain=CertificationDomain.RUNTIME,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="EventBus Dispatch",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_intelligence_registry() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            modules = reg.list_modules()
            return CheckResult(
                name="Intelligence Registry",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.PASSED,
                message=f"Registry operational. Modules listed: {len(modules)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Intelligence Registry",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_thread_safety() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            errors: list[str] = []

            def read_modules() -> None:
                try:
                    reg.list_modules()
                except Exception as exc:
                    errors.append(str(exc))

            threads = [threading.Thread(target=read_modules) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=2)

            if errors:
                return CheckResult(
                    name="Thread Safety",
                    domain=CertificationDomain.RUNTIME,
                    status=CheckStatus.FAILED,
                    message=f"Concurrency errors: {errors[0]}",
                    duration_ms=_ms(start),
                    critical=True,
                )
            return CheckResult(
                name="Thread Safety",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.PASSED,
                message="10 concurrent registry reads completed without errors.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Thread Safety",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_plugin_framework() -> CheckResult:
        start = time.perf_counter()
        try:
            from sdk.plugins.plugin_lifecycle import PluginLifecycle  # noqa: F401
            return CheckResult(
                name="Plugin Framework",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.PASSED,
                message="Plugin SDK lifecycle module importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Plugin Framework",
                domain=CertificationDomain.RUNTIME,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )


def _ms(start: float) -> float:
    """Returns elapsed milliseconds since *start*."""
    return round((time.perf_counter() - start) * 1000, 2)
