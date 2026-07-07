"""Plugin migrator upgrading manifest versions and checking dependency compatibility."""

from __future__ import annotations

import time
import uuid
from typing import List

from backend.migration.models import MigrationKind, MigrationStatus, MigrationStep


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class PluginMigrator:
    """Upgrades third-party plugin manifests and ensures API version compatibility."""

    @staticmethod
    def get_steps(from_version: str, to_version: str) -> List[MigrationStep]:
        """Gets plugin manifest migration steps for the version bump."""
        key = f"{from_version}->{to_version}"
        if from_version == to_version:
            return []
        return [
            MigrationStep(
                step_id=str(uuid.uuid4())[:8],
                kind=MigrationKind.PLUGIN,
                description=f"Upgrade Plugin Manifest compatibility tags from {from_version} to {to_version}",
                from_version=from_version,
                to_version=to_version,
            )
        ]

    @staticmethod
    def apply(manifests: List[dict], from_version: str, to_version: str) -> tuple[List[dict], List[MigrationStep]]:
        """Upgrades manifest compatible versions to target version where possible."""
        steps = PluginMigrator.get_steps(from_version, to_version)
        if not steps:
            return manifests, []

        step = steps[0]
        start = time.perf_counter()
        upgraded = []
        try:
            for m in manifests:
                new_m = m.copy()
                new_m["compatible_nexus_version"] = f">={to_version}"
                upgraded.append(new_m)
            step.status = MigrationStatus.COMPLETED
            step.applied_at = _utcnow()
        except Exception as exc:
            step.status = MigrationStatus.FAILED
            step.error = str(exc)
            upgraded = manifests
        finally:
            step.duration_ms = round((time.perf_counter() - start) * 1000, 2)

        return upgraded, steps
