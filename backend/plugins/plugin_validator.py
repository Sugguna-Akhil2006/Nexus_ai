"""Validates plugin manifest configurations against platform rules."""

import re
from backend.plugins.models import PluginManifest


class PluginValidator:
    """Performs validation checks on plugin manifests, versions, and configurations."""

    def __init__(self, platform_version: str = "1.0.0") -> None:
        self.platform_version = platform_version

    def validate_manifest(self, manifest: PluginManifest) -> bool:
        """Validates all manifest constraints, throwing ValueError on violations."""
        # 1. Check name format (alphanumeric and underscore only)
        if not re.match(r"^[a-zA-Z0-9_-]+$", manifest.name):
            raise ValueError(f"Plugin name '{manifest.name}' contains invalid characters.")

        # 2. Check version format (semantic versioning basic format)
        if not re.match(r"^\d+\.\d+\.\d+", manifest.version):
            raise ValueError(f"Plugin version '{manifest.version}' must follow semantic versioning (X.Y.Z).")

        # 3. Check minimum runtime version compatibility
        if not self._is_compatible(manifest.min_runtime_version, self.platform_version):
            raise ValueError(
                f"Plugin '{manifest.name}' requires minimum runtime version '{manifest.min_runtime_version}', "
                f"but platform version is '{self.platform_version}'."
            )

        # 4. Check capabilities are populated
        if not manifest.capabilities:
            raise ValueError(f"Plugin '{manifest.name}' must declare at least one capability.")

        # 5. Check entry point is defined
        if not manifest.entry_point:
            raise ValueError(f"Plugin '{manifest.name}' must specify a valid Python entry_point.")

        return True

    def _is_compatible(self, min_ver: str, current_ver: str) -> bool:
        """Compares version tags basic numerical splits."""
        try:
            min_parts = [int(x) for x in min_ver.split(".")]
            cur_parts = [int(x) for x in current_ver.split(".")]
            
            # Pad sequences
            while len(min_parts) < 3: min_parts.append(0)
            while len(cur_parts) < 3: cur_parts.append(0)
            
            return cur_parts >= min_parts
        except Exception:
            return False
