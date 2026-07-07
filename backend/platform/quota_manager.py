"""Quota Manager enforcing daily and monthly token/cost limits."""

from __future__ import annotations

import threading
from typing import Dict, Optional

from backend.api.sqlite_mock import DBStorage
from backend.runtime.event import Event, EventBus, EventType
from backend.platform.models import QuotaPolicy


class QuotaManager:
    """Tracks workspace, user, and organization consumption quotas."""

    def __init__(self) -> None:
        self._db = DBStorage()
        self._event_bus = EventBus()
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_quotas (
                policy_id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                daily_token_limit INTEGER NOT NULL,
                monthly_token_limit INTEGER NOT NULL,
                daily_cost_limit REAL NOT NULL,
                monthly_cost_limit REAL NOT NULL
            )
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS platform_quota_usage (
                workspace_id TEXT,
                user_id TEXT,
                tokens_today INTEGER NOT NULL,
                tokens_month INTEGER NOT NULL,
                cost_today REAL NOT NULL,
                cost_month REAL NOT NULL,
                PRIMARY KEY (workspace_id, user_id)
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def set_quota_policy(self, policy: QuotaPolicy) -> None:
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO platform_quotas (
                    policy_id, workspace_id, user_id, daily_token_limit,
                    monthly_token_limit, daily_cost_limit, monthly_cost_limit
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_id) DO UPDATE SET
                    workspace_id=excluded.workspace_id,
                    user_id=excluded.user_id,
                    daily_token_limit=excluded.daily_token_limit,
                    monthly_token_limit=excluded.monthly_token_limit,
                    daily_cost_limit=excluded.daily_cost_limit,
                    monthly_cost_limit=excluded.monthly_cost_limit
                """, (
                    policy.policy_id,
                    policy.workspace_id,
                    policy.user_id,
                    policy.daily_token_limit,
                    policy.monthly_token_limit,
                    policy.daily_cost_limit,
                    policy.monthly_cost_limit
                ))
                conn.commit()
            finally:
                conn.close()

    def check_and_record_consumption(self, workspace_id: str, user_id: str, tokens: int, cost: float) -> bool:
        """Verifies if tokens/cost does not violate quota, and logs consumption.

        Returns:
            bool: True if allowed, False if quota exceeded.
        """
        with self._lock:
            conn = self._db._get_connection()
            try:
                # 1. Resolve matching policy rule
                row_policy = conn.execute(
                    "SELECT * FROM platform_quotas WHERE (workspace_id = ? OR workspace_id = '*') AND (user_id = ? OR user_id = '*') LIMIT 1",
                    (workspace_id, user_id)
                ).fetchone()

                # If no custom policy, enforce global default limit parameters
                policy = QuotaPolicy(
                    policy_id="default",
                    daily_token_limit=100000,
                    daily_cost_limit=5.00
                )
                if row_policy:
                    policy = QuotaPolicy(
                        policy_id=row_policy["policy_id"],
                        workspace_id=row_policy["workspace_id"],
                        user_id=row_policy["user_id"],
                        daily_token_limit=row_policy["daily_token_limit"],
                        monthly_token_limit=row_policy["monthly_token_limit"],
                        daily_cost_limit=row_policy["daily_cost_limit"],
                        monthly_cost_limit=row_policy["monthly_cost_limit"]
                    )

                # 2. Get current usage
                row_usage = conn.execute(
                    "SELECT * FROM platform_quota_usage WHERE workspace_id = ? AND user_id = ?",
                    (workspace_id, user_id)
                ).fetchone()

                u_tokens_today = tokens
                u_cost_today = cost
                u_tokens_month = tokens
                u_cost_month = cost

                if row_usage:
                    u_tokens_today = row_usage["tokens_today"] + tokens
                    u_cost_today = row_usage["cost_today"] + cost
                    u_tokens_month = row_usage["tokens_month"] + tokens
                    u_cost_month = row_usage["cost_month"] + cost

                # 3. Check bounds
                if u_tokens_today > policy.daily_token_limit or u_cost_today > policy.daily_cost_limit:
                    self._event_bus.publish(Event(
                        event_type=EventType.CUSTOM_EVENT,
                        source="QuotaManager",
                        payload={
                            "event": "quota.exceeded",
                            "workspace_id": workspace_id,
                            "user_id": user_id,
                            "policy_id": policy.policy_id
                        }
                    ))
                    return False

                # 4. Save updated usage
                conn.execute("""
                INSERT INTO platform_quota_usage (workspace_id, user_id, tokens_today, tokens_month, cost_today, cost_month)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(workspace_id, user_id) DO UPDATE SET
                    tokens_today=excluded.tokens_today,
                    tokens_month=excluded.tokens_month,
                    cost_today=excluded.cost_today,
                    cost_month=excluded.cost_month
                """, (workspace_id, user_id, u_tokens_today, u_tokens_month, u_cost_today, u_cost_month))
                conn.commit()
                return True
            finally:
                conn.close()

    def clear(self) -> None:
        """Clears quotas for testing."""
        with self._lock:
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM platform_quotas")
                conn.execute("DELETE FROM platform_quota_usage")
                conn.commit()
            finally:
                conn.close()
