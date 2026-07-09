"""Unit and integration tests for Enterprise Multi-Tenant Management."""

from __future__ import annotations

import unittest
from datetime import datetime

from backend.tenant.models import TenantLimits, TenantSettings, TenantStatus
from backend.tenant.tenant_context import TenantContext
from backend.tenant.tenant_limits import TenantLimitsValidator
from backend.tenant.tenant_manager import TenantManager
from backend.tenant.tenant_registry import TenantRegistry
from backend.tenant.tenant_resolver import TenantResolver
from backend.tenant.tenant_settings import TenantSettingsValidator
from backend.tenant.tenant_storage import TenantStorageGuard


class TestTenantRegistry(unittest.TestCase):
    """Verifies SQLite registry CRUD operations."""

    def setUp(self) -> None:
        self.registry = TenantRegistry(db_path=":memory:")

    def test_crud_flow(self) -> None:
        t = self.registry.create_tenant("tenant-1", "Org 1")
        self.assertEqual(t.name, "Org 1")
        self.assertEqual(t.status, TenantStatus.ACTIVE)

        retrieved = self.registry.get_tenant("tenant-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Org 1")

        # Update status
        t.status = TenantStatus.SUSPENDED
        self.registry.save_tenant(t)
        retrieved_updated = self.registry.get_tenant("tenant-1")
        self.assertEqual(retrieved_updated.status, TenantStatus.SUSPENDED)


class TestTenantContext(unittest.TestCase):
    """Verifies async-safe context variable scopes."""

    def test_set_and_reset(self) -> None:
        self.assertIsNone(TenantContext.get_tenant_id())

        token = TenantContext.set_tenant_id("tenant-abc")
        self.assertEqual(TenantContext.get_tenant_id(), "tenant-abc")

        TenantContext.reset_tenant_id(token)
        self.assertIsNone(TenantContext.get_tenant_id())


class TestTenantResolver(unittest.TestCase):
    """Verifies request resolver headers and parameters parsing."""

    def test_resolve_from_query(self) -> None:
        # Mock minimal request-like object
        class MockRequest:
            def __init__(self) -> None:
                self.headers = {}
                self.query_params = {"tenant_id": "tenant-query"}

        req = MockRequest()
        tenant_id = TenantResolver.resolve_tenant_id(req)
        self.assertEqual(tenant_id, "tenant-query")


class TestTenantStorage(unittest.TestCase):
    """Verifies query re-writing injection scopes."""

    def test_apply_tenant_scope_inactive(self) -> None:
        sql = "SELECT * FROM users"
        scoped_sql, params = TenantStorageGuard.apply_tenant_scope(sql, ())
        self.assertEqual(scoped_sql, sql)
        self.assertEqual(len(params), 0)

    def test_apply_tenant_scope_active(self) -> None:
        token = TenantContext.set_tenant_id("tenant-123")
        try:
            sql = "SELECT * FROM users"
            scoped_sql, params = TenantStorageGuard.apply_tenant_scope(sql, ())
            self.assertIn("tenant_id = ?", scoped_sql)
            self.assertEqual(params[0], "tenant-123")
        finally:
            TenantContext.reset_tenant_id(token)


class TestTenantLimitsAndSettings(unittest.TestCase):
    """Verifies resource checks and model whitelisting validation."""

    def test_limits_validator(self) -> None:
        limits = TenantLimits(api_rate_limit=10, max_concurrent_jobs=3)
        self.assertTrue(TenantLimitsValidator.is_api_allowed(limits, 5))
        self.assertFalse(TenantLimitsValidator.is_api_allowed(limits, 15))

        self.assertTrue(TenantLimitsValidator.is_concurrency_allowed(limits, 2))
        self.assertFalse(TenantLimitsValidator.is_concurrency_allowed(limits, 4))

    def test_settings_validator(self) -> None:
        settings = TenantSettings(allowed_models=["gpt-4", "gemini-1.5"])
        self.assertTrue(TenantSettingsValidator.is_model_allowed(settings, "gpt-4"))
        self.assertFalse(TenantSettingsValidator.is_model_allowed(settings, "claude-3"))


class TestTenantManagerE2E(unittest.TestCase):
    """Verifies high-level manager lifecycle operations and event logging."""

    def setUp(self) -> None:
        self.manager = TenantManager(db_path=":memory:")

    def test_tenant_lifecycle(self) -> None:
        t = self.manager.create_tenant("tenant-mgr", "Manager Org")
        self.assertEqual(t.name, "Manager Org")

        # Suspend
        success = self.manager.suspend_tenant("tenant-mgr")
        self.assertTrue(success)
        retrieved = self.manager.get_tenant("tenant-mgr")
        self.assertEqual(retrieved.status, TenantStatus.SUSPENDED)
