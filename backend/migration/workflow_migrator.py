"""Workflow migrator upgrading workflow schemas and version tags."""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict, List

from backend.migration.models import MigrationKind, MigrationStatus, MigrationStep


def _utcnow() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class WorkflowMigrator:
    """Upgrades workflow schemas and step structures between version configurations."""

    @staticmethod
    def get_steps(from_version: str, to_version: str) -> List[MigrationStep]:
        """Gets workflow upgrade steps."""
        if from_version == to_version:
            return []
        return [
            MigrationStep(
                step_id=str(uuid.uuid4())[:8],
                kind=MigrationKind.WORKFLOW,
                description=f"Upgrade Workflow Step schemas from {from_version} to {to_version}",
                from_version=from_version,
                to_version=to_version,
            )
        ]

    @staticmethod
    def apply(workflows: List[Dict[str, Any]], from_version: str, to_version: str) -> tuple[List[Dict[str, Any]], List[MigrationStep]]:
        """Upgrades workflow structures and step definition blocks."""
        steps = WorkflowMigrator.get_steps(from_version, to_version)
        if not steps:
            return workflows, []

        step = steps[0]
        start = time.perf_counter()
        upgraded = []
        try:
            for wf in workflows:
                new_wf = wf.copy()
                new_wf["version"] = to_version
                # Standardize step schemas
                steps_list = new_wf.get("steps", [])
                for s in steps_list:
                    s.setdefault("retry_policy", {"max_retries": 3, "backoff": "exponential"})
                new_wf["steps"] = steps_list
                upgraded.append(new_wf)
            step.status = MigrationStatus.COMPLETED
            step.applied_at = _utcnow()
        except Exception as exc:
            step.status = MigrationStatus.FAILED
            step.error = str(exc)
            upgraded = workflows
        finally:
            step.duration_ms = round((time.perf_counter() - start) * 1000, 2)

        return upgraded, steps
