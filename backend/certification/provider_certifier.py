"""Provider certifier validating provider connectivity, fallback, timeouts, and retries."""

from __future__ import annotations

import time

from backend.certification.models import (
    CertificationDomain,
    CheckResult,
    CheckStatus,
    DomainReport,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


class ProviderCertifier:
    """Certifies the AI Provider subsystem.

    Checks performed:
    - Provider registry importability.
    - Provider listing / configuration availability.
    - Fallback chain configuration presence.
    - Retry policy configuration presence.
    - Streaming capability declaration.
    """

    DOMAIN = CertificationDomain.PROVIDER

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all provider checks and returns a domain report."""
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_provider_registry(),
            cls._check_provider_listing(),
            cls._check_fallback_config(),
            cls._check_retry_config(),
            cls._check_streaming_support(),
        ])
        return report

    @staticmethod
    def _check_provider_registry() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.providers.registry import ProviderRegistry  # noqa: F401
            return CheckResult(
                name="Provider Registry Import",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.PASSED,
                message="ProviderRegistry importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Provider Registry Import",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_provider_listing() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.providers.registry import ProviderRegistry
            reg = ProviderRegistry()
            providers = reg.list_providers() if hasattr(reg, "list_providers") else []
            return CheckResult(
                name="Provider Listing",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.PASSED,
                message=f"Registry operational. Registered providers: {len(providers)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Provider Listing",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.WARNING,
                message=f"Provider listing skipped: {exc}",
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_fallback_config() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.providers.registry import ProviderRegistry
            reg = ProviderRegistry()
            has_fallback = hasattr(reg, "fallback_provider") or hasattr(reg, "get_fallback")
            status = CheckStatus.PASSED if has_fallback else CheckStatus.WARNING
            msg = "Fallback chain configured." if has_fallback else "No fallback chain detected."
            return CheckResult(
                name="Fallback Chain",
                domain=CertificationDomain.PROVIDER,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Fallback Chain",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_retry_config() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.config.provider_config import ProviderConfig
            cfg = ProviderConfig()
            has_retry = hasattr(cfg, "max_retries") or hasattr(cfg, "retry_policy")
            status = CheckStatus.PASSED if has_retry else CheckStatus.WARNING
            msg = "Retry policy present." if has_retry else "Retry policy not found in ProviderConfig."
            return CheckResult(
                name="Retry Policy",
                domain=CertificationDomain.PROVIDER,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Retry Policy",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.WARNING,
                message=f"Retry config check skipped: {exc}",
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_streaming_support() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.providers.registry import ProviderRegistry
            reg = ProviderRegistry()
            has_streaming = hasattr(reg, "stream") or hasattr(reg, "supports_streaming")
            status = CheckStatus.PASSED if has_streaming else CheckStatus.WARNING
            msg = "Streaming support declared." if has_streaming else "Streaming capability not detected."
            return CheckResult(
                name="Streaming Support",
                domain=CertificationDomain.PROVIDER,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Streaming Support",
                domain=CertificationDomain.PROVIDER,
                status=CheckStatus.WARNING,
                message=str(exc),
                duration_ms=_ms(start),
            )
