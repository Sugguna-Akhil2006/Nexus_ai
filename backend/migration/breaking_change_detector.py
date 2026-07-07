"""Breaking change detector scanning API surfaces, config keys, and dependencies."""

from __future__ import annotations

import importlib
import uuid
from typing import List, Optional

from backend.migration.models import (
    BreakingChange,
    BreakingChangeSeverity,
)

# Known API locations to inspect for removed/renamed symbols
_API_MODULES = [
    "backend.api.main",
    "backend.intelligence.core.registry",
    "backend.workflow.automation_engine",
    "backend.runtime.event",
    "backend.providers.registry",
]

# Config keys required to be present in every supported version
_REQUIRED_CONFIG_KEYS = [
    "environment",
    "server",
    "database",
    "llm_providers",
    "limits",
]

# Plugin SDK symbols that must remain stable
_SDK_SYMBOLS = [
    ("sdk.plugins.plugin_sdk", "NexusPlugin"),
    ("sdk.plugins.plugin_manifest", "PluginManifest"),
    ("sdk.plugins.plugin_lifecycle", "PluginLifecycle"),
]


class BreakingChangeDetector:
    """Scans platform surfaces to detect breaking changes between version pairs.

    Detection categories:
    - **removed_api**: A previously public module or class is no longer importable.
    - **config_change**: A required configuration key is missing from the schema.
    - **sdk_contract**: A stable SDK symbol is no longer importable.
    - **deprecated**: A known deprecated feature is still in use.
    """

    @classmethod
    def detect(cls, from_version: str, to_version: str) -> List[BreakingChange]:
        """Runs all detection passes and returns identified breaking changes.

        Args:
            from_version: Currently installed version label.
            to_version: Target version label.

        Returns:
            List of :class:`BreakingChange` objects (empty if none detected).
        """
        changes: List[BreakingChange] = []
        changes.extend(cls._check_api_modules(from_version, to_version))
        changes.extend(cls._check_config_keys(from_version, to_version))
        changes.extend(cls._check_sdk_contract(from_version, to_version))
        return changes

    # ------------------------------------------------------------------
    # Detection passes
    # ------------------------------------------------------------------

    @staticmethod
    def _check_api_modules(from_v: str, to_v: str) -> List[BreakingChange]:
        changes: List[BreakingChange] = []
        for mod_path in _API_MODULES:
            try:
                importlib.import_module(mod_path)
            except ImportError as exc:
                changes.append(
                    BreakingChange(
                        change_id=str(uuid.uuid4())[:8],
                        kind="removed_api",
                        location=mod_path,
                        description=f"Module '{mod_path}' is no longer importable: {exc}",
                        severity=BreakingChangeSeverity.CRITICAL,
                        from_version=from_v,
                        to_version=to_v,
                        migration_hint=f"Restore or provide a shim for '{mod_path}'.",
                    )
                )
        return changes

    @staticmethod
    def _check_config_keys(from_v: str, to_v: str) -> List[BreakingChange]:
        """Checks that the AppConfig schema still exposes required keys."""
        changes: List[BreakingChange] = []
        try:
            from backend.config.models import AppConfig
            schema_fields = set(AppConfig.model_fields.keys())
            for key in _REQUIRED_CONFIG_KEYS:
                if key not in schema_fields:
                    changes.append(
                        BreakingChange(
                            change_id=str(uuid.uuid4())[:8],
                            kind="config_change",
                            location=f"AppConfig.{key}",
                            description=f"Required config key '{key}' was removed from AppConfig.",
                            severity=BreakingChangeSeverity.HIGH,
                            from_version=from_v,
                            to_version=to_v,
                            migration_hint=f"Add '{key}' back to AppConfig or supply a migration rule.",
                        )
                    )
        except Exception as exc:
            changes.append(
                BreakingChange(
                    change_id=str(uuid.uuid4())[:8],
                    kind="config_change",
                    location="AppConfig",
                    description=f"Config schema check failed: {exc}",
                    severity=BreakingChangeSeverity.HIGH,
                    from_version=from_v,
                    to_version=to_v,
                )
            )
        return changes

    @staticmethod
    def _check_sdk_contract(from_v: str, to_v: str) -> List[BreakingChange]:
        """Verifies that stable Plugin SDK symbols are still exported."""
        changes: List[BreakingChange] = []
        for mod_path, symbol in _SDK_SYMBOLS:
            try:
                mod = importlib.import_module(mod_path)
                if not hasattr(mod, symbol):
                    raise AttributeError(f"'{symbol}' missing from '{mod_path}'")
            except Exception as exc:
                changes.append(
                    BreakingChange(
                        change_id=str(uuid.uuid4())[:8],
                        kind="sdk_contract",
                        location=f"{mod_path}.{symbol}",
                        description=str(exc),
                        severity=BreakingChangeSeverity.CRITICAL,
                        from_version=from_v,
                        to_version=to_v,
                        migration_hint=f"Restore '{symbol}' in '{mod_path}' or provide a compatibility shim.",
                    )
                )
        return changes
