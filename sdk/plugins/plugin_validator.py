"""Plugin manifest and code validator checking compatibility and structure rules."""

from __future__ import annotations

import re
from typing import List

from sdk.plugins.models import PluginManifestModel, PluginValidationResult


# Minimum platform version this SDK targets
_PLATFORM_VERSION = (1, 0, 0)

# Allowed semver pattern
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _parse_version(ver: str) -> tuple[int, ...]:
    """Parses a semver string into a comparable integer tuple."""
    clean = ver.lstrip(">=<~^").strip()
    try:
        return tuple(int(x) for x in clean.split("."))
    except ValueError:
        return (0, 0, 0)


class PluginValidator:
    """Validates plugin manifests against structural and compatibility rules.

    Validation rules checked:
    - ``plugin_id`` must be non-empty snake_case.
    - ``version`` must follow semver ``MAJOR.MINOR.PATCH``.
    - ``compatible_nexus_version`` constraint must be satisfiable.
    - ``entry_point`` must be a non-empty dotted path.
    - ``author`` should be provided (warning if absent).
    """

    @staticmethod
    def validate(manifest: PluginManifestModel) -> PluginValidationResult:
        """Validates the plugin manifest and returns a detailed result.

        Args:
            manifest: Manifest to validate.

        Returns:
            :class:`PluginValidationResult` with errors and warnings.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # plugin_id: snake_case, non-empty
        if not manifest.plugin_id:
            errors.append("'plugin_id' must not be empty.")
        elif not re.match(r"^[a-z][a-z0-9_]*$", manifest.plugin_id):
            errors.append(
                f"'plugin_id' must be snake_case (got '{manifest.plugin_id}')."
            )

        # name: non-empty
        if not manifest.name.strip():
            errors.append("'name' must not be empty.")

        # version: semver
        if not _SEMVER_RE.match(manifest.version):
            errors.append(
                f"'version' must follow semver MAJOR.MINOR.PATCH (got '{manifest.version}')."
            )

        # compatible_nexus_version: parse and compare
        compat_ver = _parse_version(manifest.compatible_nexus_version)
        if compat_ver > _PLATFORM_VERSION:
            errors.append(
                f"'compatible_nexus_version' {manifest.compatible_nexus_version} "
                f"is newer than the platform version {'.'.join(str(v) for v in _PLATFORM_VERSION)}."
            )

        # entry_point: non-empty and dotted path
        if not manifest.entry_point.strip():
            errors.append("'entry_point' must not be empty.")
        elif "." not in manifest.entry_point:
            warnings.append(
                f"'entry_point' '{manifest.entry_point}' does not look like a dotted module path."
            )

        # author: warn if missing
        if not manifest.author.strip():
            warnings.append("'author' is not specified — recommended for marketplace plugins.")

        return PluginValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
