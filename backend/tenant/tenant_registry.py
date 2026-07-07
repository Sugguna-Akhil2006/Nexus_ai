"""Tenant registry managing database entries for multi-tenancy organizations."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from backend.api.sqlite_mock import DBStorage
from backend.tenant.models import Tenant, TenantLimits, TenantSettings, TenantStatus


class TenantRegistry:
    """Manages SQLite CRUD operations for tenant structures."""

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        self.db = DBStorage(db_path)
        self._init_table()

    def _init_table(self) -> None:
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenants (
                tenant_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL,
                settings TEXT NOT NULL,
                limits TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        settings: Optional[TenantSettings] = None,
        limits: Optional[TenantLimits] = None,
    ) -> Tenant:
        """Creates a new organization tenant."""
        t = Tenant(
            tenant_id=tenant_id,
            name=name,
            status=TenantStatus.ACTIVE,
            settings=settings or TenantSettings(),
            limits=limits or TenantLimits(),
            created_at=datetime.utcnow().isoformat(),
        )
        self.save_tenant(t)
        return t

    def save_tenant(self, tenant: Tenant) -> None:
        """Saves a tenant details to SQLite."""
        conn = self.db._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO tenants
                (tenant_id, name, status, settings, limits, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    tenant.tenant_id,
                    tenant.name,
                    tenant.status.value,
                    tenant.settings.model_dump_json(),
                    tenant.limits.model_dump_json(),
                    tenant.created_at,
                ),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            conn.close()

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieves a tenant by ID."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return Tenant(
                tenant_id=r["tenant_id"],
                name=r["name"],
                status=TenantStatus(r["status"]),
                settings=TenantSettings.model_validate_json(r["settings"]),
                limits=TenantLimits.model_validate_json(r["limits"]),
                created_at=r["created_at"],
            )
        except Exception:
            return None
        finally:
            conn.close()

    def list_tenants(self) -> List[Tenant]:
        """Lists all registered tenants."""
        conn = self.db._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenants")
            rows = cursor.fetchall()
            tenants = []
            for r in rows:
                tenants.append(
                    Tenant(
                        tenant_id=r["tenant_id"],
                        name=r["name"],
                        status=TenantStatus(r["status"]),
                        settings=TenantSettings.model_validate_json(r["settings"]),
                        limits=TenantLimits.model_validate_json(r["limits"]),
                        created_at=r["created_at"],
                    )
                )
            return tenants
        except Exception:
            return []
        finally:
            conn.close()
