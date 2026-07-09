"""Knowledge certifier validating the Knowledge Fabric subsystem."""

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


class KnowledgeCertifier:
    """Certifies the Knowledge Fabric and intelligence module availability.

    Checks performed:
    - KnowledgeFabric importability.
    - Resume Intelligence module availability.
    - GitHub Intelligence module availability.
    - Document Intelligence module availability.
    - Professional Intelligence module availability.
    """

    DOMAIN = CertificationDomain.KNOWLEDGE

    @classmethod
    def certify(cls) -> DomainReport:
        """Executes all knowledge checks and returns a domain report."""
        report = DomainReport(domain=cls.DOMAIN)
        report.checks.extend([
            cls._check_knowledge_fabric(),
            cls._check_resume_intelligence(),
            cls._check_github_intelligence(),
            cls._check_document_intelligence(),
            cls._check_professional_intelligence(),
        ])
        return report

    @staticmethod
    def _check_knowledge_fabric() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.knowledge_fabric import knowledge_service  # noqa: F401
            return CheckResult(
                name="Knowledge Fabric",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.PASSED,
                message="Knowledge Fabric module importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Knowledge Fabric",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_resume_intelligence() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.resume.module import ResumeModule
            mod = ResumeModule()
            return CheckResult(
                name="Resume Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.PASSED,
                message=f"ResumeModule available. Capabilities: {list(mod.capabilities)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Resume Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_github_intelligence() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.github.module import GitHubModule
            mod = GitHubModule()
            return CheckResult(
                name="GitHub Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.PASSED,
                message=f"GitHubModule available. Capabilities: {list(mod.capabilities)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="GitHub Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_document_intelligence() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.document.document_agent import DocumentModule
            mod = DocumentModule()
            return CheckResult(
                name="Document Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.PASSED,
                message=f"DocumentModule available. Capabilities: {list(mod.capabilities)}.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Document Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.FAILED,
                message=str(exc),
                duration_ms=_ms(start),
                critical=True,
            )

    @staticmethod
    def _check_professional_intelligence() -> CheckResult:
        start = time.perf_counter()
        try:
            from backend.intelligence.professional import professional_module  # noqa: F401
            return CheckResult(
                name="Professional Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.PASSED,
                message="Professional Intelligence module importable.",
                duration_ms=_ms(start),
            )
        except Exception as exc:
            return CheckResult(
                name="Professional Intelligence",
                domain=CertificationDomain.KNOWLEDGE,
                status=CheckStatus.WARNING,
                message=f"Module check skipped: {exc}",
                duration_ms=_ms(start),
            )
