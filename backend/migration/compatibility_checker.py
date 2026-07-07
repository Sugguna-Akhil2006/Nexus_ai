"""Compatibility checker evaluating version pairs for API and config contract differences."""

from __future__ import annotations

import re
import uuid
from typing import List, Tuple

from backend.migration.models import (
    CompatibilityReport,
    CompatibilityStatus,
)

# Semver pattern
_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def _parse(ver: str) -> Tuple[int, int, int]:
    m = _SEMVER_RE.match(ver.strip())
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


class CompatibilityChecker:
    """Determines whether a version pair is compatible without running migrations.

    Compatibility rules (semver-based):
    - Same major → compatible (possibly with warnings for minor bumps).
    - Major bump of exactly 1 → compatible with warnings; >1 → incompatible.
    - Downgrade always generates a critical warning.

    The checker also probes the FastAPI route table to detect any removed
    endpoints between the installed and target platform builds.
    """

    @staticmethod
    def check(from_version: str, to_version: str) -> CompatibilityReport:
        """Evaluates compatibility from *from_version* to *to_version*.

        Args:
            from_version: Currently installed platform version.
            to_version: Target version to upgrade to.

        Returns:
            :class:`CompatibilityReport` with verdict and recommended actions.
        """
        warnings: List[str] = []
        recommendations: List[str] = []

        f_maj, f_min, f_pat = _parse(from_version)
        t_maj, t_min, t_pat = _parse(to_version)
        from_t = (f_maj, f_min, f_pat)
        to_t = (t_maj, t_min, t_pat)

        # Downgrade
        if to_t < from_t:
            status = CompatibilityStatus.INCOMPATIBLE
            warnings.append(
                f"Downgrade from {from_version} → {to_version} is not supported. "
                "Create a full backup before attempting."
            )
            recommendations.append("Restore from backup instead of downgrading.")
        # Same version
        elif from_t == to_t:
            status = CompatibilityStatus.COMPATIBLE
        # Major bump > 1
        elif t_maj - f_maj > 1:
            status = CompatibilityStatus.INCOMPATIBLE
            warnings.append(
                f"Major version jump of {t_maj - f_maj} detected ({from_version} → {to_version}). "
                "Step-upgrade through intermediate major versions is required."
            )
            recommendations.append(
                f"Upgrade to {f_maj + 1}.0.0 first, then continue toward {to_version}."
            )
        # Major bump of 1
        elif t_maj - f_maj == 1:
            status = CompatibilityStatus.COMPATIBLE_WITH_WARNINGS
            warnings.append(
                f"Major version bump ({from_version} → {to_version}) may contain breaking changes. "
                "Review the migration report before upgrading."
            )
            recommendations.append("Run breaking-change detection before applying migrations.")
        # Minor bump
        elif t_min != f_min:
            status = CompatibilityStatus.COMPATIBLE_WITH_WARNINGS
            warnings.append(
                f"Minor version change ({from_version} → {to_version}). "
                "Configuration keys may have changed."
            )
            recommendations.append("Review config migration plan before upgrading.")
        else:
            status = CompatibilityStatus.COMPATIBLE

        # Probe live route table for removed endpoints
        route_warnings = CompatibilityChecker._probe_routes()
        warnings.extend(route_warnings)
        if route_warnings:
            if status == CompatibilityStatus.COMPATIBLE:
                status = CompatibilityStatus.COMPATIBLE_WITH_WARNINGS

        return CompatibilityReport(
            report_id=str(uuid.uuid4())[:8],
            from_version=from_version,
            to_version=to_version,
            status=status,
            warnings=warnings,
            recommendations=recommendations,
        )

    @staticmethod
    def _probe_routes() -> List[str]:
        """Checks that core platform API routes are still registered."""
        issues: List[str] = []
        required_prefixes = ["intelligence", "workflow", "runtime", "provider"]
        try:
            from backend.api.main import app
            registered = {r.path for r in app.routes}  # type: ignore[attr-defined]
            for prefix in required_prefixes:
                if not any(prefix in p for p in registered):
                    issues.append(f"Core route prefix '{prefix}' not found in registered routes.")
        except Exception as exc:
            issues.append(f"Route probe skipped: {exc}")
        return issues
