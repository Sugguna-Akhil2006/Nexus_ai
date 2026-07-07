"""Plugin permission evaluator that enforces declared permission scopes."""

from __future__ import annotations

from typing import List, Set

from sdk.plugins.models import PluginManifestModel, PluginPermission


class PluginPermissions:
    """Evaluates and enforces the permission scopes declared in a plugin manifest.

    Permissions are evaluated at install time (static check) and may be
    queried at runtime to guard sensitive operations.
    """

    # Permissions that require explicit platform approval before granting
    HIGH_RISK: Set[PluginPermission] = {
        PluginPermission.FILESYSTEM,
        PluginPermission.NETWORK,
        PluginPermission.SANDBOX,
        PluginPermission.ENVIRONMENT_VARIABLES,
    }

    @staticmethod
    def evaluate(manifest: PluginManifestModel) -> List[str]:
        """Returns a list of warnings for high-risk permission requests.

        Args:
            manifest: Plugin manifest to audit.

        Returns:
            List of warning messages (empty if all permissions are safe).
        """
        warnings: List[str] = []
        for perm in manifest.permissions:
            if perm in PluginPermissions.HIGH_RISK:
                warnings.append(
                    f"Plugin '{manifest.plugin_id}' requests high-risk permission: '{perm.value}'. "
                    "Requires platform administrator approval."
                )
        return warnings

    @staticmethod
    def has_permission(manifest: PluginManifestModel, permission: PluginPermission) -> bool:
        """Returns True if the plugin has declared the requested permission.

        Args:
            manifest: Plugin manifest.
            permission: Permission to check.

        Returns:
            True if declared, False otherwise.
        """
        return permission in manifest.permissions

    @staticmethod
    def assert_permission(manifest: PluginManifestModel, permission: PluginPermission) -> None:
        """Raises PermissionError if the plugin has not declared the permission.

        Args:
            manifest: Plugin manifest.
            permission: Required permission.

        Raises:
            PermissionError: If permission is not declared.
        """
        if not PluginPermissions.has_permission(manifest, permission):
            raise PermissionError(
                f"Plugin '{manifest.plugin_id}' attempted to use '{permission.value}' "
                "without declaring it in its manifest."
            )
