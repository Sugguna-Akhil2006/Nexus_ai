"""Automation scheduler handling cron schedules and next trigger runs."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.workflow_library.models import AutomationSchedule


class AutomationScheduler:
    """Manages cron-triggered automated jobs in SQLite."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS automation_schedules (
                schedule_id TEXT PRIMARY KEY,
                template_id TEXT NOT NULL,
                cron_expression TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                next_run_at TEXT
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def schedule_template(self, template_id: str, cron_expression: str) -> AutomationSchedule:
        """Adds a cron schedule trigger for a template."""
        # Simple mocked next execution time
        next_run = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        sched = AutomationSchedule(
            schedule_id=f"sch-{uuid.uuid4().hex[:8]}",
            template_id=template_id,
            cron_expression=cron_expression,
            enabled=True,
            next_run_at=next_run,
        )
        self.save_schedule(sched)
        return sched

    def save_schedule(self, schedule: AutomationSchedule) -> None:
        """Saves a schedule details to SQLite."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO automation_schedules
                (schedule_id, template_id, cron_expression, enabled, next_run_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    schedule.schedule_id,
                    schedule.template_id,
                    schedule.cron_expression,
                    1 if schedule.enabled else 0,
                    schedule.next_run_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def list_schedules(self) -> List[AutomationSchedule]:
        """Lists all registered schedules."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM automation_schedules")
            rows = cursor.fetchall()
            schedules = []
            for r in rows:
                schedules.append(
                    AutomationSchedule(
                        schedule_id=r["schedule_id"],
                        template_id=r["template_id"],
                        cron_expression=r["cron_expression"],
                        enabled=bool(r["enabled"]),
                        next_run_at=r["next_run_at"],
                    )
                )
            return schedules
        except Exception:
            return []
        finally:
            conn.close()
DefinitionPath = "automation_scheduler.py"
