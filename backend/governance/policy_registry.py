"""Policy registry responsible for discovery and persistence of governance rules."""

from __future__ import annotations

import sqlite3
import threading
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.governance.models import PolicyRule


class PolicyRegistry:
    """Thread-safe registry managing policy constraints rules."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "PolicyRegistry":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._lock:
            if getattr(self, "_initialized", False):
                return
            self._db = DBStorage()
            self._policies: Dict[str, PolicyRule] = {}
            self._init_db()
            self._load_policies()
            self._initialized = True

    def _init_db(self) -> None:
        conn = self._db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS governance_policies (
                policy_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                workspace_id TEXT NOT NULL,
                allowed_modules TEXT NOT NULL,
                allowed_models TEXT NOT NULL,
                allowed_providers TEXT NOT NULL,
                allowed_plugins TEXT NOT NULL,
                max_tokens INTEGER NOT NULL,
                max_cost REAL NOT NULL,
                max_execution_time REAL NOT NULL,
                is_active INTEGER NOT NULL
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def _load_policies(self) -> None:
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM governance_policies").fetchall()
            for r in rows:
                rule = PolicyRule(
                    policy_id=r["policy_id"],
                    name=r["name"],
                    workspace_id=r["workspace_id"],
                    allowed_modules=r["allowed_modules"].split(","),
                    allowed_models=r["allowed_models"].split(","),
                    allowed_providers=r["allowed_providers"].split(","),
                    allowed_plugins=r["allowed_plugins"].split(","),
                    max_tokens=r["max_tokens"],
                    max_cost=r["max_cost"],
                    max_execution_time=r["max_execution_time"],
                    is_active=bool(r["is_active"])
                )
                self._policies[rule.policy_id] = rule

            # Register a default global policy rule if database is empty
            if not self._policies:
                default_rule = PolicyRule(
                    policy_id="default-global",
                    name="Global Default Governance Rule",
                    workspace_id="*",
                    allowed_modules=["*"],
                    allowed_models=["*"],
                    allowed_providers=["*"],
                    allowed_plugins=["*"],
                    max_tokens=8192,
                    max_cost=1.00,
                    max_execution_time=120.0,
                    is_active=True
                )
                self.register_policy(default_rule)
        finally:
            conn.close()

    def register_policy(self, rule: PolicyRule) -> None:
        """Saves a policy rule to the registry database and cache."""
        with self._lock:
            self._policies[rule.policy_id] = rule
            conn = self._db._get_connection()
            try:
                conn.execute("""
                INSERT INTO governance_policies (
                    policy_id, name, workspace_id, allowed_modules, allowed_models,
                    allowed_providers, allowed_plugins, max_tokens, max_cost,
                    max_execution_time, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(policy_id) DO UPDATE SET
                    name=excluded.name,
                    workspace_id=excluded.workspace_id,
                    allowed_modules=excluded.allowed_modules,
                    allowed_models=excluded.allowed_models,
                    allowed_providers=excluded.allowed_providers,
                    allowed_plugins=excluded.allowed_plugins,
                    max_tokens=excluded.max_tokens,
                    max_cost=excluded.max_cost,
                    max_execution_time=excluded.max_execution_time,
                    is_active=excluded.is_active
                """, (
                    rule.policy_id,
                    rule.name,
                    rule.workspace_id,
                    ",".join(rule.allowed_modules),
                    ",".join(rule.allowed_models),
                    ",".join(rule.allowed_providers),
                    ",".join(rule.allowed_plugins),
                    rule.max_tokens,
                    rule.max_cost,
                    rule.max_execution_time,
                    1 if rule.is_active else 0
                ))
                conn.commit()
            finally:
                conn.close()

    def get_policy(self, policy_id: str) -> Optional[PolicyRule]:
        """Retrieves a single policy rule by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def list_policies(self, workspace_id: Optional[str] = None) -> List[PolicyRule]:
        """Lists active policies. Filterable by workspace."""
        with self._lock:
            active_rules = [p for p in self._policies.values() if p.is_active]
            if not workspace_id:
                return active_rules
            return [
                p for p in active_rules
                if p.workspace_id == "*" or p.workspace_id == workspace_id
            ]

    def clear(self) -> None:
        """Clears all policies for testing purposes."""
        with self._lock:
            self._policies.clear()
            conn = self._db._get_connection()
            try:
                conn.execute("DELETE FROM governance_policies")
                conn.commit()
            finally:
                conn.close()
