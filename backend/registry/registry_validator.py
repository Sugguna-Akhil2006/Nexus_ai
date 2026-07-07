"""Registry validator validating capability semantic versioning and compatibility constraints."""

from __future__ import annotations

import warnings
from typing import Optional

from backend.registry.registry_models import CapabilityMetadata, SemVer


class RegistryValidator:
    """Validates capability semver compatibility, deprecations, and upgrades."""

    def validate_semver(self, ver_str: str) -> bool:
        """Checks if the version string complies with semantic versioning standards."""
        try:
            SemVer.parse(ver_str)
            return True
        except Exception:
            return False

    def is_compatible(self, cap_meta: CapabilityMetadata, target_runtime_version: str) -> bool:
        """Verifies if the capability is compatible with the target runtime version."""
        if not cap_meta.compatibilities or "*" in cap_meta.compatibilities:
            return True

        try:
            target = SemVer.parse(target_runtime_version)
            for c_str in cap_meta.compatibilities:
                c = SemVer.parse(c_str)
                # Enforce major version compatibility match
                if c.major == target.major:
                    return True
        except Exception:
            pass

        return False

    def check_upgrade_path(self, cap_meta: CapabilityMetadata) -> Optional[str]:
        """Checks for deprecation and returns suggested upgrade version if available."""
        if cap_meta.is_deprecated:
            if cap_meta.upgrade_path:
                warnings.warn(
                    f"Capability '{cap_meta.capability_id}' is deprecated. Upgrade path is available to: '{cap_meta.upgrade_path}'.",
                    DeprecationWarning,
                    stacklevel=2
                )
                return cap_meta.upgrade_path
        return None
