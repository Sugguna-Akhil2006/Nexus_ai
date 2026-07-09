"""Version manager parsing and incrementing semantic versions."""

from __future__ import annotations

import re
from typing import Optional

from backend.release_builder.models import ReleaseType, VersionInfo


class VersionManager:
    """Manages parsing, formatting, and incrementing semantic versions (SemVer)."""

    SEMVER_REGEX = re.compile(
        r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
        r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
        r"(?:\+(?P<buildmetadata>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
    )

    @classmethod
    def parse_version(cls, version_str: str) -> Optional[VersionInfo]:
        """Parses a version string into VersionInfo.

        Returns:
            VersionInfo if valid, otherwise None.
        """
        match = cls.SEMVER_REGEX.match(version_str)
        if not match:
            return None
        gd = match.groupdict()
        return VersionInfo(
            major=int(gd["major"]),
            minor=int(gd["minor"]),
            patch=int(gd["patch"]),
            pre_release=gd.get("prerelease"),
            build_metadata=gd.get("buildmetadata"),
        )

    @classmethod
    def increment_version(
        self,
        current: str,
        release_type: ReleaseType,
        pre_release_label: Optional[str] = "rc",
    ) -> str:
        """Increments version numbers according to release target definitions."""
        v = self.parse_version(current)
        if not v:
            return "1.0.0"

        major, minor, patch = v.major, v.minor, v.patch

        if release_type == ReleaseType.STABLE:
            # Drop pre-release suffix
            return f"{major}.{minor}.{patch}"

        if release_type == ReleaseType.HOTFIX:
            patch += 1
            return f"{major}.{minor}.{patch}"

        if release_type == ReleaseType.NIGHTLY:
            import time
            date_str = time.strftime("%Y%m%d")
            return f"{major}.{minor}.{patch}-nightly.{date_str}"

        # Default Release Candidate (RC)
        if v.pre_release and pre_release_label in v.pre_release:
            # e.g. "rc.1" -> increment number
            match = re.search(r"\d+$", v.pre_release)
            if match:
                num = int(match.group()) + 1
                prefix = v.pre_release[:match.start()]
                new_pre = f"{prefix}{num}"
            else:
                new_pre = f"{v.pre_release}.1"
        else:
            new_pre = f"{pre_release_label}.1"

        return f"{major}.{minor}.{patch}-{new_pre}"
DefinitionPath = "version_manager.py"
