"""SDK and API version constants with compatibility validation."""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Final, List, Optional, Tuple


SDK_VERSION: Final[str] = "1.0.0"
API_VERSION: Final[str] = "v1"
MIN_SUPPORTED_API_VERSION: Final[str] = "v1"
MAX_SUPPORTED_API_VERSION: Final[str] = "v1"

DEPRECATED_API_VERSIONS: Final[List[str]] = []


@dataclass(frozen=True)
class VersionInfo:
    """Version metadata exposed to SDK consumers.

    Attributes:
        sdk_version: Current SDK release version.
        api_version: Target API version prefix.
        min_supported_api_version: Oldest compatible API version.
        max_supported_api_version: Newest compatible API version.
    """

    sdk_version: str
    api_version: str
    min_supported_api_version: str
    max_supported_api_version: str


def get_version_info() -> VersionInfo:
    """Returns current SDK and API version metadata.

    Returns:
        VersionInfo: Frozen version metadata record.
    """
    return VersionInfo(
        sdk_version=SDK_VERSION,
        api_version=API_VERSION,
        min_supported_api_version=MIN_SUPPORTED_API_VERSION,
        max_supported_api_version=MAX_SUPPORTED_API_VERSION,
    )


def _parse_version(version: str) -> Tuple[int, ...]:
    """Parses a version string into numeric tuple components.

    Args:
        version: Version label such as ``v1`` or ``1.2.3``.

    Returns:
        Tuple of integer version components.
    """
    normalized = version.lstrip("v")
    parts: List[int] = []
    for segment in normalized.split("."):
        if segment.isdigit():
            parts.append(int(segment))
    return tuple(parts) if parts else (0,)


def validate_api_version(api_version: str) -> None:
    """Validates that the requested API version is supported by this SDK.

    Args:
        api_version: API version prefix (e.g. ``v1``).

    Raises:
        ValueError: If the API version is outside the supported range.
    """
    requested = _parse_version(api_version)
    minimum = _parse_version(MIN_SUPPORTED_API_VERSION)
    maximum = _parse_version(MAX_SUPPORTED_API_VERSION)

    if requested < minimum or requested > maximum:
        raise ValueError(
            f"API version '{api_version}' is not supported. "
            f"Supported range: {MIN_SUPPORTED_API_VERSION}–{MAX_SUPPORTED_API_VERSION}."
        )

    if api_version in DEPRECATED_API_VERSIONS:
        warnings.warn(
            f"API version '{api_version}' is deprecated and will be removed in a future release.",
            DeprecationWarning,
            stacklevel=2,
        )


def check_server_compatibility(server_version: Optional[str]) -> bool:
    """Checks whether a server-reported API version is compatible with this SDK.

    Args:
        server_version: Version string returned by the server, or ``None``.

    Returns:
        True when the server version is within the supported range.
    """
    if not server_version:
        return True
    try:
        validate_api_version(server_version)
        return True
    except ValueError:
        return False
