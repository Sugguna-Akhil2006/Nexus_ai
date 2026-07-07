"""Compatibility checker validating framework version and OS support."""

import sys
from typing import Dict, Any, Optional
from backend.marketplace.models import PackageMetadata
from backend.marketplace.version_manager import VersionManager


class CompatibilityChecker:
    """Verifies package requirements against local system specifications."""

    def __init__(self, core_version: str = "1.0.0", platform_os: Optional[str] = None) -> None:
        self.core_version = core_version
        self.platform_os = platform_os or sys.platform

    def is_compatible(self, metadata: PackageMetadata) -> bool:
        """Determines if the package matches core and platform constraints."""
        compat = metadata.compatibility
        if not compat:
            return True

        # Check core framework version
        min_core = compat.get("min_core_version")
        if min_core:
            if VersionManager.compare_versions(self.core_version, min_core) < 0:
                return False

        # Check Operating System compatibility
        supported_os = compat.get("os")
        if supported_os:
            # Normalize system name (e.g., win32 -> windows)
            current_os = "windows" if "win" in self.platform_os.lower() else "linux" if "lin" in self.platform_os.lower() else "macos" if "dar" in self.platform_os.lower() else self.platform_os.lower()
            supported_os_normalized = [os.lower() for os in supported_os]
            if current_os not in supported_os_normalized:
                return False

        return True
