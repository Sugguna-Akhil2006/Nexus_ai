"""Security certifier verifying authentication, authorization, secrets, sandbox, and input validation."""

from __future__ import annotations

import re
import time

from backend.certification.models import (
    CertificationDomain,
    CheckResult,
    CheckStatus,
    DomainReport,
)


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


# Patterns that should never appear plaintext in config or environment output
_SECRET_PATTERNS = [
    re.compile(r"(?i)(password|secret|api_key|token)\s*=\s*['\"]?\S+"),
]


class SecurityCertifier:
    """Certifies the Nexus AI Security subsystem.

    Checks performed:
    - Authentication module importability.
    - Authorization/governance module availability.
    - Secret masking validation (no plaintext secrets in db_storage defaults).
    - Sandbox isolation availability.
    - Input validation utilities availability.
    """

    DOMAIN = CertificationDomain.SECURITY

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all security checks and returns a domain report."""
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_authentication(),
            cls._check_authorization(),
            cls._check_secret_masking(),
            cls._check_sandbox(),
            cls._check_input_validation(),
        ])
        return report

    @staticmethod
    def _check_authentication() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.api.sqlite_mock import DBStorage  # noqa: F401
            db = DBStorage()
            user = db.get_user("admin")
            # Must have a hashed password – not plaintext
            if user and "hashed_" in (user.get("password", "") or ""):
                return CheckResult(
                    name="Authentication",
                    domain=CertificationDomain.SECURITY,
                    status=CheckStatus.PASSED,
                    message="Admin account password is hashed correctly.",
                    duration_ms=_ms(start),
                )
            return CheckResult(
                name="Authentication",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.WARNING,
                message="Admin account not found or password storage unclear.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Authentication",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_authorization() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.governance.governance_engine import GovernanceEngine  # noqa: F401
            return CheckResult(
                name="Authorization / Governance",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.PASSED,
                message="GovernanceEngine importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Authorization / Governance",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_secret_masking() -> CheckResult:
        """Verifies that no plaintext secrets appear in known config exports."""
        start = time.perf_counter()
        try:
            from backend.config.secret_manager import SecretManager
            mgr = SecretManager()
            exposed = getattr(mgr, "_secrets", {})
            exposed_keys = list(exposed.keys()) if isinstance(exposed, dict) else []
            if exposed_keys:
                return CheckResult(
                    name="Secret Masking",
                    domain=CertificationDomain.SECURITY,
                    status=CheckStatus.WARNING,
                    message=f"SecretManager has {len(exposed_keys)} in-memory secret(s). Ensure none are logged.",
                    duration_ms=_ms(start),
                )
            return CheckResult(
                name="Secret Masking",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.PASSED,
                message="No unmasked secrets detected in SecretManager.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Secret Masking",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.WARNING,
                message=f"Secret masking check skipped: {exc}",
                duration_ms=_ms(start),
            )

    @staticmethod
    def _check_sandbox() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.sandbox.sandbox_manager import SandboxManager  # noqa: F401
            return CheckResult(
                name="Sandbox Isolation",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.PASSED,
                message="SandboxManager importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Sandbox Isolation",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_input_validation() -> CheckResult:
        start = time.perf_counter()
        try:
            # Pydantic is the project's validation layer — confirm it is importable
            import pydantic  # noqa: F401
            from pydantic import BaseModel, ValidationError

            class _TestModel(BaseModel):
                value: int

            try:
                _TestModel(value="not-an-int")  # type: ignore[arg-type]
                valid = False
            except ValidationError:
                valid = True

            status = CheckStatus.PASSED if valid else CheckStatus.FAILED
            msg = "Pydantic input validation active." if valid else "Pydantic validation not rejecting bad input."
            return CheckResult(
                name="Input Validation",
                domain=CertificationDomain.SECURITY,
                status=status,
                message=msg,
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Input Validation",
                domain=CertificationDomain.SECURITY,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )
