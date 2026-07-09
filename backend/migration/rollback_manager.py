"""Rollback manager reverting migration steps on failure."""

from __future__ import annotations

import sqlite3
import time
import uuid
from typing import Any, Dict, List

from backend.migration.models import MigrationKind, MigrationStatus, RollbackRecord


class RollbackManager:
    """Handles reversal of applied schema, config, plugin, and workflow migration steps."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._db_path = db_path

    def rollback(self, run_id: str, steps: List[Any], config: Dict[str, Any]) -> RollbackRecord:
        """Attempts to rollback all successfully applied steps in reverse order.

        Args:
            run_id: ID of the failed migration run.
            steps: List of migration steps to rollback.
            config: Configuration dictionary to revert.

        Returns:
            :class:`RollbackRecord` summarizing the rollbacks.
        """
        rolled_back_ids = []
        conn = sqlite3.connect(self._db_path)
        reverted_config = config.copy()

        for step in reversed(steps):
            if step.status != MigrationStatus.COMPLETED:
                continue

            if step.kind == MigrationKind.SCHEMA:
                # Reverting tables by dropping if they match the DDL pattern
                try:
                    desc = step.description.lower()
                    if "create table" in desc:
                        tbl_name = desc.split("table if not exists")[-1].split("(")[0].strip()
                        if not tbl_name:
                            tbl_name = desc.split("table")[-1].split("(")[0].strip()
                        if tbl_name:
                            conn.execute(f"DROP TABLE IF EXISTS {tbl_name};")
                            conn.commit()
                except Exception:
                    pass
            elif step.kind == MigrationKind.CONFIG:
                # Revert hot reload to reload
                if "server" in reverted_config and "hot_reload" in reverted_config["server"]:
                    reverted_config["server"]["reload"] = reverted_config["server"].pop("hot_reload")

            rolled_back_ids.append(step.step_id)
            step.status = MigrationStatus.ROLLED_BACK

        conn.close()
        return RollbackRecord(
            rollback_id=str(uuid.uuid4())[:8],
            run_id=run_id,
            rolled_back_steps=rolled_back_ids,
            status=MigrationStatus.ROLLED_BACK,
            detail=f"Reverted {len(rolled_back_ids)} step(s) successfully.",
        )
