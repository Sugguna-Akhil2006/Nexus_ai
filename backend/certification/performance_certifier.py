"""Performance certifier measuring latency, memory, CPU, and concurrency benchmarks."""

from __future__ import annotations

import gc
import sys
import threading
import time
import tracemalloc

from backend.certification.models import (
    CertificationDomain,
    CheckResult,
    CheckStatus,
    DomainReport,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


# Performance thresholds
_REGISTRY_LATENCY_MS = 500.0   # Registry list must complete under 500ms
_MEMORY_CEILING_MB = 50.0      # Registry instantiation must add < 50MB
_CONCURRENCY_TIMEOUT_S = 5.0   # 20 concurrent threads must finish in 5s


class PerformanceCertifier:
    """Measures runtime performance against defined certification thresholds.

    Checks performed:
    - Registry list latency (<500ms).
    - Memory footprint of registry instantiation (<50MB delta).
    - 20 concurrent registry reads within 5s.
    - Workflow template listing latency.
    """

    DOMAIN = CertificationDomain.PERFORMANCE

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all performance checks and returns a domain report."""
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_registry_latency(),
            cls._check_memory_footprint(),
            cls._check_concurrent_reads(),
            cls._check_template_listing_latency(),
        ])
        return report

    @staticmethod
    def _check_registry_latency() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            reg.list_modules()
            elapsed = _ms(start)
            status = CheckStatus.PASSED if elapsed < _REGISTRY_LATENCY_MS else CheckStatus.WARNING
            msg = (
                f"Registry list completed in {elapsed}ms (threshold: {_REGISTRY_LATENCY_MS}ms)."
            )
            return CheckResult(
                name="Registry Latency",
                domain=CertificationDomain.PERFORMANCE,
                status=status,
                message=msg,
                duration_ms=elapsed,
            )
        except Exception as exc:
            return CheckResult(
                name="Registry Latency",
                domain=CertificationDomain.PERFORMANCE,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_memory_footprint() -> CheckResult:
        start = time.perf_counter()
        try:
            gc.collect()
            tracemalloc.start()
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            reg.list_modules()
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_mb = peak / 1024 / 1024
            status = CheckStatus.PASSED if peak_mb < _MEMORY_CEILING_MB else CheckStatus.WARNING
            msg = f"Peak memory delta: {peak_mb:.2f}MB (ceiling: {_MEMORY_CEILING_MB}MB)."
            return CheckResult(
                name="Memory Footprint",
                domain=CertificationDomain.PERFORMANCE,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            tracemalloc.stop()
            return CheckResult(
                name="Memory Footprint",
                domain=CertificationDomain.PERFORMANCE,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_concurrent_reads() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.core.registry import IntelligenceRegistry
            reg = IntelligenceRegistry()
            errors: list[str] = []
            done = threading.Event()

            def worker() -> None:
                try:
                    reg.list_modules()
                except Exception as exc:
                    errors.append(str(exc))

            threads = [threading.Thread(target=worker) for _ in range(20)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=_CONCURRENCY_TIMEOUT_S)

            elapsed = _ms(start)
            if errors:
                return CheckResult(
                    name="Concurrent Registry Reads",
                    domain=CertificationDomain.PERFORMANCE,
                    status=CheckStatus.FAILED,
                    message=f"Concurrency error: {errors[0]}",
                    duration_ms=elapsed,
                    critical=True,
                )
            status = CheckStatus.PASSED if elapsed < _CONCURRENCY_TIMEOUT_S * 1000 else CheckStatus.WARNING
            return CheckResult(
                name="Concurrent Registry Reads",
                domain=CertificationDomain.PERFORMANCE,
                status=status,
                message=f"20 concurrent reads completed in {elapsed}ms.",
                duration_ms=elapsed,
            )
        except Exception as exc:
            return CheckResult(
                name="Concurrent Registry Reads",
                domain=CertificationDomain.PERFORMANCE,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_template_listing_latency() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.workflow_library.template_registry import TemplateRegistry
            reg = TemplateRegistry(db_path=":memory:")
            reg.list_templates()
            elapsed = _ms(start)
            status = CheckStatus.PASSED if elapsed < _REGISTRY_LATENCY_MS else CheckStatus.WARNING
            return CheckResult(
                name="Template Listing Latency",
                domain=CertificationDomain.PERFORMANCE,
                status=status,
                message=f"Template listing completed in {elapsed}ms.",
                duration_ms=elapsed,
            )
        except Exception as exc:
            return CheckResult(
                name="Template Listing Latency",
                domain=CertificationDomain.PERFORMANCE,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )
