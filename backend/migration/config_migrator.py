"""Config migrator transforming AppConfig dictionaries between platform versions."""

from __future__ import annotations

import time
import uuid
from typing import Any, Callable, Dict, List

from backend.migration.models import MigrationKind, MigrationStatus, MigrationStep


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Migration rule type: takes an old config dict, returns a new config dict
# ---------------------------------------------------------------------------
ConfigTransform = Callable[[Dict[str, Any]], Dict[str, Any]]


# ---------------------------------------------------------------------------
# Versioned transform registry
# ---------------------------------------------------------------------------

def _1_0_to_1_1(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """1.0.0 → 1.1.0: add limits.concurrent_executions default."""
    cfg.setdefault("limits", {})
    cfg["limits"].setdefault("concurrent_executions", 10)
    return cfg


def _1_1_to_1_2(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """1.1.0 → 1.2.0: rename server.reload → server.hot_reload."""
    if "server" in cfg and "reload" in cfg["server"]:
        cfg["server"]["hot_reload"] = cfg["server"].pop("reload")
    return cfg


def _1_0_to_2_0(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """1.0.0 → 2.0.0: full upgrade path (composite transform)."""
    cfg = _1_0_to_1_1(cfg)
    cfg = _1_1_to_1_2(cfg)
    # 2.0 adds feature_flags section
    cfg.setdefault("feature_flags", {})
    return cfg


_TRANSFORMS: Dict[str, ConfigTransform] = {
    "1.0.0->1.1.0": _1_0_to_1_1,
    "1.1.0->1.2.0": _1_1_to_1_2,
    "1.0.0->2.0.0": _1_0_to_2_0,
}


class ConfigMigrator:
    """Transforms AppConfig dictionaries between version schemas.

    Transforms are applied in-memory; the caller is responsible for
    persisting the result.  An audit trail of :class:`MigrationStep` objects
    is returned alongside the transformed config.
    """

    @staticmethod
    def get_steps(from_version: str, to_version: str) -> List[MigrationStep]:
        """Returns config migration steps for the version pair.

        Args:
            from_version: Source version.
            to_version: Target version.

        Returns:
            List of migration steps (empty if no transform registered).
        """
        key = f"{from_version}->{to_version}"
        if key not in _TRANSFORMS:
            return []
        return [
            MigrationStep(
                step_id=str(uuid.uuid4())[:8],
                kind=MigrationKind.CONFIG,
                description=f"Transform AppConfig {from_version} → {to_version}",
                from_version=from_version,
                to_version=to_version,
            )
        ]

    @staticmethod
    def apply(
        config: Dict[str, Any],
        from_version: str,
        to_version: str,
    ) -> tuple[Dict[str, Any], List[MigrationStep]]:
        """Applies the registered config transform.

        Args:
            config: Current configuration dictionary.
            from_version: Source version.
            to_version: Target version.

        Returns:
            Tuple of (transformed_config, steps_with_status).
        """
        steps = ConfigMigrator.get_steps(from_version, to_version)
        key = f"{from_version}->{to_version}"
        transform = _TRANSFORMS.get(key)

        if not transform or not steps:
            return config, steps

        step = steps[0]
        start = time.perf_counter()
        try:
            import copy
            result = transform(copy.deepcopy(config))
            step.status = MigrationStatus.COMPLETED
            step.applied_at = _utcnow()
            step.duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return result, steps
        except Exception as exc:
            step.status = MigrationStatus.FAILED
            step.error = str(exc)
            step.duration_ms = round((time.perf_counter() - start) * 1000, 2)
            return config, steps
