"""Scorecard calculator converting domain scores into certification levels."""

from __future__ import annotations

from typing import List

from backend.certification.models import (
    CertificationLevel,
    CertificationRun,
    CheckStatus,
    DomainReport,
)

# Score thresholds per certification level
_THRESHOLDS: dict[CertificationLevel, int] = {
    CertificationLevel.ENTERPRISE: 95,
    CertificationLevel.GOLD: 85,
    CertificationLevel.SILVER: 70,
    CertificationLevel.BRONZE: 50,
}

# Point deductions per failure type
_DEDUCTION_CRITICAL = 20
_DEDUCTION_FAILED = 5
_DEDUCTION_WARNING = 1


class Scorecard:
    """Calculates overall platform certification score and awards a level.

    Scoring rules:
    - Start at 100 points.
    - Critical failures deduct 20 points each (capped at domain score = 0).
    - Regular failures deduct 5 points each.
    - Warnings deduct 1 point each.
    - Overall score is the weighted average of all domain scores.
    """

    @staticmethod
    def compute_domain_score(report: DomainReport) -> int:
        """Scores a single domain from 0-100.

        Args:
            report: Domain report with completed checks.

        Returns:
            Integer score between 0 and 100.
        """
        score = 100
        for check in report.checks:
            if check.status == CheckStatus.FAILED:
                deduction = _DEDUCTION_CRITICAL if check.critical else _DEDUCTION_FAILED
                score -= deduction
            elif check.status == CheckStatus.WARNING:
                score -= _DEDUCTION_WARNING
        return max(0, score)

    @staticmethod
    def compute_overall(domain_reports: List[DomainReport]) -> int:
        """Computes the weighted average score across all domains.

        Args:
            domain_reports: All domain reports from the run.

        Returns:
            Integer score between 0 and 100.
        """
        if not domain_reports:
            return 0
        scores = [Scorecard.compute_domain_score(r) for r in domain_reports]
        return round(sum(scores) / len(scores))

    @staticmethod
    def award_level(score: int) -> CertificationLevel:
        """Maps a numeric score to a :class:`CertificationLevel`.

        Args:
            score: Overall score (0-100).

        Returns:
            Appropriate certification level.
        """
        for level, threshold in _THRESHOLDS.items():
            if score >= threshold:
                return level
        return CertificationLevel.NONE

    @staticmethod
    def build_recommendations(domain_reports: List[DomainReport]) -> List[str]:
        """Derives improvement suggestions from failed and warning checks.

        Args:
            domain_reports: All domain reports.

        Returns:
            List of human-readable recommendation strings.
        """
        recommendations: List[str] = []
        for report in domain_reports:
            for check in report.checks:
                if check.status == CheckStatus.FAILED:
                    prefix = "CRITICAL: " if check.critical else "Fix: "
                    recommendations.append(
                        f"{prefix}[{report.domain.value}] {check.name} — {check.message}"
                    )
                elif check.status == CheckStatus.WARNING:
                    recommendations.append(
                        f"Improve: [{report.domain.value}] {check.name} — {check.message}"
                    )
        return recommendations

    @classmethod
    def finalize(cls, run: CertificationRun) -> CertificationRun:
        """Populates aggregate fields on a completed :class:`CertificationRun`.

        Args:
            run: Run with all domain reports populated.

        Returns:
            Run with overall_score, certification_level, and totals filled in.
        """
        for report in run.domain_reports:
            report.score = cls.compute_domain_score(report)
            report.critical_failures = [
                f"{c.name}: {c.message}"
                for c in report.checks
                if c.status == CheckStatus.FAILED and c.critical
            ]
            report.warnings = [
                f"{c.name}: {c.message}"
                for c in report.checks
                if c.status == CheckStatus.WARNING
            ]

        run.overall_score = cls.compute_overall(run.domain_reports)
        run.certification_level = cls.award_level(run.overall_score)
        run.total_checks = sum(len(r.checks) for r in run.domain_reports)
        run.total_passed = sum(
            1 for r in run.domain_reports for c in r.checks if c.status == CheckStatus.PASSED
        )
        run.total_failed = sum(
            1 for r in run.domain_reports for c in r.checks if c.status == CheckStatus.FAILED
        )
        run.total_warnings = sum(
            1 for r in run.domain_reports for c in r.checks if c.status == CheckStatus.WARNING
        )
        run.recommended_improvements = cls.build_recommendations(run.domain_reports)
        return run
